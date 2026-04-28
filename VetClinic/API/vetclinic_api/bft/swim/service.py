from __future__ import annotations

import uuid

from vetclinic_api.bft.common.events import EventLog, ProtocolEvent
from vetclinic_api.bft.common.types import MessageKind, NodeStatus, ProtocolName
from vetclinic_api.bft.crypto.envelope import BftMessagePayload
from vetclinic_api.bft.crypto.service import CryptoService
from vetclinic_api.bft.fault_injection.models import FaultEvaluationContext
from vetclinic_api.bft.fault_injection.service import FaultInjectionService
from vetclinic_api.bft.swim.models import (
    SwimAck,
    SwimGossipUpdate,
    SwimMember,
    SwimPing,
    SwimProbeResult,
    SwimStatus,
)
from vetclinic_api.bft.swim.store import InMemorySwimStore


def is_node_eligible_for_consensus(
    swim_store: InMemorySwimStore,
    node_id: int,
) -> bool:
    try:
        member = swim_store.get_member(node_id)
    except KeyError:
        return True
    return member.status == NodeStatus.ALIVE


class SwimService:
    def __init__(
        self,
        swim_store: InMemorySwimStore,
        event_log: EventLog,
        fault_service: FaultInjectionService | None = None,
        crypto_service: CryptoService | None = None,
    ) -> None:
        self.swim_store = swim_store
        self.event_log = event_log
        self.fault_service = fault_service
        self.crypto_service = crypto_service

    def bootstrap(
        self,
        self_node_id: int,
        self_address: str,
        peers: list[str],
    ) -> list[SwimMember]:
        members = self.swim_store.bootstrap_from_config(
            self_node_id,
            self_address,
            peers,
        )
        self._event(
            node_id=self_node_id,
            message="swim_bootstrap",
            details={"members": [member.node_id for member in members]},
        )
        return members

    def ping(
        self,
        source_node_id: int,
        target_node_id: int,
        simulate_success: bool = True,
        reason: str | None = None,
    ) -> SwimProbeResult:
        if source_node_id == target_node_id:
            member = self.swim_store.mark_alive(target_node_id, reason="self_ping")
            ping = SwimPing(
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                nonce=str(uuid.uuid4()),
            )
            ack = SwimAck(
                source_node_id=target_node_id,
                target_node_id=source_node_id,
                nonce=ping.nonce,
                accepted=True,
                status=member.status,
                incarnation=member.incarnation,
                reason="self_ping",
            )
            return SwimProbeResult(
                ping=ping,
                ack=ack,
                status_before=member.status,
                status_after=member.status,
            )

        before = self._status_or_none(target_node_id)
        ping = SwimPing(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            nonce=str(uuid.uuid4()),
        )
        decision = self._evaluate_fault(
            message_kind=MessageKind.SWIM_PING,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            message_id=ping.nonce,
            metadata={"reason": reason},
        )
        fault_forced_failure = bool(
            decision and (decision.should_drop or decision.blocked_by_partition)
        )
        if decision and decision.should_delay:
            self._event(
                node_id=source_node_id,
                message="swim_ping_delay_simulated",
                details={
                    "target_node_id": target_node_id,
                    "nonce": ping.nonce,
                    "delay_ms": decision.delay_ms,
                },
            )
        if decision and decision.should_duplicate:
            self._event(
                node_id=source_node_id,
                message="swim_ping_duplicate_simulated",
                details={"target_node_id": target_node_id, "nonce": ping.nonce},
            )
        if fault_forced_failure:
            simulate_success = False
        if simulate_success:
            member = self.swim_store.mark_alive(target_node_id, reason=reason or "ack")
            signed_ping = self._sign_protocol_message(
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                message_kind=MessageKind.SWIM_PING,
                correlation_id=ping.nonce,
                body={"nonce": ping.nonce},
            )
            signed_ack = self._sign_protocol_message(
                source_node_id=target_node_id,
                target_node_id=source_node_id,
                message_kind=MessageKind.SWIM_ACK,
                correlation_id=ping.nonce,
                body={"nonce": ping.nonce, "accepted": True},
            )
            ack = SwimAck(
                source_node_id=target_node_id,
                target_node_id=source_node_id,
                nonce=ping.nonce,
                accepted=True,
                status=member.status,
                incarnation=member.incarnation,
                reason=reason,
            )
            self._event(
                node_id=source_node_id,
                message="swim_ping_ack",
                details={
                    "target_node_id": target_node_id,
                    "nonce": ping.nonce,
                    **self._signed_details(signed_ping, "signed_ping"),
                    **self._signed_details(signed_ack, "signed_ack"),
                },
            )
            self._status_event(member)
            return SwimProbeResult(
                ping=ping,
                ack=ack,
                status_before=before,
                status_after=member.status,
            )

        member = self.swim_store.mark_suspect(
            target_node_id,
            reason=reason or "missed_ack",
        )
        if member.suspicion_count >= 2:
            member = self.swim_store.mark_dead(target_node_id)
        self._event(
            node_id=source_node_id,
            message="swim_ping_missed",
            details={
                "target_node_id": target_node_id,
                "nonce": ping.nonce,
                "reason": reason,
                **self._signed_details(
                    self._sign_protocol_message(
                        source_node_id=source_node_id,
                        target_node_id=target_node_id,
                        message_kind=MessageKind.SWIM_PING,
                        correlation_id=ping.nonce,
                        body={"nonce": ping.nonce, "accepted": False},
                    ),
                    "signed_ping",
                ),
            },
        )
        self._status_event(member)
        return SwimProbeResult(
            ping=ping,
            ack=None,
            status_before=before,
            status_after=member.status,
        )

    def ping_req(
        self,
        source_node_id: int,
        intermediary_node_id: int,
        target_node_id: int,
        simulate_success: bool = True,
    ) -> SwimAck:
        target = (
            self.swim_store.mark_alive(target_node_id, reason="ping_req")
            if simulate_success
            else self.swim_store.get_member(target_node_id)
        )
        decision = self._evaluate_fault(
            message_kind=MessageKind.SWIM_ACK,
            source_node_id=intermediary_node_id,
            target_node_id=target_node_id,
            message_id=f"ping-req:{source_node_id}:{intermediary_node_id}:{target_node_id}",
            metadata={},
        )
        if decision and (decision.should_drop or decision.blocked_by_partition):
            simulate_success = False
            target = self.swim_store.get_member(target_node_id)
        ack = SwimAck(
            source_node_id=target_node_id,
            target_node_id=source_node_id,
            nonce=str(uuid.uuid4()),
            accepted=simulate_success,
            status=target.status,
            incarnation=target.incarnation,
            reason=None if simulate_success else "indirect_probe_failed",
        )
        self._event(
            node_id=intermediary_node_id,
            message="swim_ping_req",
            details={
                "source_node_id": source_node_id,
                "target_node_id": target_node_id,
                "accepted": simulate_success,
                **self._signed_details(
                    self._sign_protocol_message(
                        source_node_id=intermediary_node_id,
                        target_node_id=target_node_id,
                        message_kind=MessageKind.SWIM_ACK,
                        correlation_id=ack.nonce,
                        body={"accepted": simulate_success, "nonce": ack.nonce},
                    ),
                    "signed_ack",
                ),
            },
        )
        if simulate_success:
            self._status_event(target)
        return ack

    def gossip(
        self,
        source_node_id: int,
        updates: list[SwimGossipUpdate],
    ) -> SwimStatus:
        decision = self._evaluate_fault(
            message_kind=MessageKind.SWIM_GOSSIP,
            source_node_id=source_node_id,
            target_node_id=None,
            message_id=f"gossip:{source_node_id}:{uuid.uuid4()}",
            metadata={"updates": len(updates)},
        )
        if decision and (decision.should_drop or decision.blocked_by_partition):
            raise ValueError("SWIM gossip blocked by fault injection")
        for update in updates:
            member = self.swim_store.apply_gossip(update)
            self._status_event(member)
        self._event(
            node_id=source_node_id,
            message="swim_gossip_applied",
            details={
                "updates": len(updates),
                **self._signed_details(
                    self._sign_protocol_message(
                        source_node_id=source_node_id,
                        target_node_id=None,
                        message_kind=MessageKind.SWIM_GOSSIP,
                        correlation_id=None,
                        body={"updates": [update.model_dump(mode="json") for update in updates]},
                    ),
                    "signed_gossip",
                ),
            },
        )
        return self.status(source_node_id)

    def suspect(self, node_id: int, reason: str = "manual_suspect") -> SwimMember:
        member = self.swim_store.mark_suspect(node_id, reason)
        self._status_event(member)
        return member

    def mark_dead(self, node_id: int, reason: str = "manual_dead") -> SwimMember:
        member = self.swim_store.mark_dead(node_id, reason)
        self._status_event(member)
        return member

    def mark_alive(self, node_id: int, reason: str = "manual_alive") -> SwimMember:
        member = self.swim_store.mark_alive(node_id, reason=reason)
        self._status_event(member)
        return member

    def mark_recovering(
        self,
        node_id: int,
        reason: str = "manual_recovering",
    ) -> SwimMember:
        member = self.swim_store.mark_recovering(node_id, reason)
        self._status_event(member)
        return member

    def probe_demo(
        self,
        target_node_id: int,
        self_node_id: int,
        total_nodes: int,
        fail_direct: bool = False,
        fail_indirect: bool = False,
    ) -> SwimProbeResult:
        del total_nodes
        direct = self.ping(
            self_node_id,
            target_node_id,
            simulate_success=not fail_direct,
            reason="probe_demo_direct",
        )
        if direct.ack:
            return direct

        indirect_acks: list[SwimAck] = []
        intermediaries = [
            member.node_id
            for member in self.swim_store.list_members()
            if member.status == NodeStatus.ALIVE
            and member.node_id not in {self_node_id, target_node_id}
        ][:2]
        for intermediary in intermediaries:
            ack = self.ping_req(
                self_node_id,
                intermediary,
                target_node_id,
                simulate_success=not fail_indirect,
            )
            indirect_acks.append(ack)
            if ack.accepted:
                member = self.swim_store.mark_alive(target_node_id, reason="indirect_ack")
                return SwimProbeResult(
                    ping=direct.ping,
                    ack=ack,
                    status_before=direct.status_before,
                    status_after=member.status,
                    indirect_probes=indirect_acks,
                )

        member = self.swim_store.get_member(target_node_id)
        if member.status != NodeStatus.DEAD and member.suspicion_count >= 2:
            member = self.swim_store.mark_dead(target_node_id)
            self._status_event(member)
        return SwimProbeResult(
            ping=direct.ping,
            ack=None,
            status_before=direct.status_before,
            status_after=member.status,
            indirect_probes=indirect_acks,
        )

    def status(self, self_node_id: int) -> SwimStatus:
        return self.swim_store.status(self_node_id)

    def clear(self) -> None:
        self.swim_store.clear()

    def _status_or_none(self, node_id: int) -> NodeStatus | None:
        try:
            return self.swim_store.get_member(node_id).status
        except KeyError:
            return None

    def _status_event(self, member: SwimMember) -> None:
        message = {
            NodeStatus.ALIVE: "swim_member_alive",
            NodeStatus.SUSPECT: "swim_member_suspect",
            NodeStatus.DEAD: "swim_member_dead",
            NodeStatus.RECOVERING: "swim_member_recovering",
        }[member.status]
        self._event(
            node_id=member.node_id,
            message=message,
            details={
                "node_id": member.node_id,
                "status": member.status.value,
                "incarnation": member.incarnation,
                "suspicion_count": member.suspicion_count,
            },
        )

    def _event(self, node_id: int | None, message: str, details: dict) -> None:
        self.event_log.append(
            ProtocolEvent(
                event_id=str(uuid.uuid4()),
                node_id=node_id,
                protocol=ProtocolName.SWIM,
                operation_id=None,
                status=None,
                message=message,
                details=details,
            )
        )

    def _evaluate_fault(
        self,
        *,
        message_kind: MessageKind,
        source_node_id: int | None,
        target_node_id: int | None,
        message_id: str | None,
        metadata: dict,
    ):
        if self.fault_service is None:
            return None
        return self.fault_service.evaluate(
            FaultEvaluationContext(
                protocol=ProtocolName.SWIM,
                message_kind=message_kind,
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                operation_id=None,
                message_id=message_id,
                metadata=metadata,
            )
        )

    def _sign_protocol_message(
        self,
        *,
        source_node_id: int,
        target_node_id: int | None,
        message_kind: MessageKind,
        correlation_id: str | None,
        body: dict,
    ):
        if self.crypto_service is None:
            return None
        payload = BftMessagePayload(
            protocol=ProtocolName.SWIM,
            message_kind=message_kind,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            operation_id=None,
            correlation_id=correlation_id,
            body=body,
        )
        try:
            return self.crypto_service.sign_message(payload, source_node_id)
        except KeyError:
            self.crypto_service.key_registry.ensure_demo_keys([source_node_id])
            return self.crypto_service.sign_message(payload, source_node_id)

    @staticmethod
    def _signed_details(message, prefix: str) -> dict:
        if message is None:
            return {}
        return {
            f"{prefix}_message_id": message.message_id,
            f"{prefix}_message": message.model_dump(mode="json"),
        }
