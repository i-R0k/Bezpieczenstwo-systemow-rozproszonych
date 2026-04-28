from __future__ import annotations

import uuid

from vetclinic_api.bft.checkpointing.store import InMemoryCheckpointStore
from vetclinic_api.bft.common.events import EventLog, ProtocolEvent
from vetclinic_api.bft.common.operations import InMemoryOperationStore
from vetclinic_api.bft.common.types import MessageKind, NodeStatus, OperationStatus, ProtocolName
from vetclinic_api.bft.crypto.envelope import BftMessagePayload
from vetclinic_api.bft.crypto.service import CryptoService
from vetclinic_api.bft.recovery.models import (
    RecoveryResult,
    RecoveryStatus,
    StateTransferRequest,
    StateTransferResponse,
)
from vetclinic_api.bft.recovery.store import InMemoryRecoveryStore
from vetclinic_api.bft.swim.store import InMemorySwimStore


class RecoveryService:
    def __init__(
        self,
        operation_store: InMemoryOperationStore,
        checkpoint_store: InMemoryCheckpointStore,
        recovery_store: InMemoryRecoveryStore,
        swim_store: InMemorySwimStore,
        event_log: EventLog,
        crypto_service: CryptoService | None = None,
    ) -> None:
        self.operation_store = operation_store
        self.checkpoint_store = checkpoint_store
        self.recovery_store = recovery_store
        self.swim_store = swim_store
        self.event_log = event_log
        self.crypto_service = crypto_service

    def request_state_transfer(
        self,
        node_id: int,
        checkpoint_id: str | None = None,
        reason: str = "stale_or_crashed_node",
    ) -> StateTransferRequest:
        certificate = (
            self.checkpoint_store.get_certificate(checkpoint_id)
            if checkpoint_id
            else self.checkpoint_store.latest_certificate()
        )
        if certificate is None:
            raise ValueError("No checkpoint certificate available for state transfer")
        try:
            self.swim_store.mark_recovering(node_id, reason="state_transfer_requested")
        except KeyError:
            self.swim_store.upsert_member(
                node_id=node_id,
                address=f"node-{node_id}",
                status=NodeStatus.RECOVERING,
            )
        request = StateTransferRequest(
            request_id=str(uuid.uuid4()),
            node_id=node_id,
            checkpoint_id=certificate.checkpoint_id,
            reason=reason,
        )
        self.recovery_store.add_transfer(request)
        self._event(
            node_id=node_id,
            message="state_transfer_requested",
            details={
                "request_id": request.request_id,
                "checkpoint_id": request.checkpoint_id,
                **self._signed_details(
                    self._sign_state_transfer(
                        source_node_id=node_id,
                        target_node_id=None,
                        correlation_id=request.request_id,
                        body=request.model_dump(mode="json"),
                    )
                ),
            },
        )
        return request

    def build_state_transfer_response(
        self,
        request: StateTransferRequest,
    ) -> StateTransferResponse:
        certificate = self.checkpoint_store.get_certificate(request.checkpoint_id)
        snapshot = self.checkpoint_store.get_snapshot(certificate.snapshot_id)
        committed_after = [
            operation.operation_id
            for operation in self.operation_store.list(limit=10000)
            if operation.status in {OperationStatus.COMMITTED, OperationStatus.EXECUTED}
            and operation.operation_id not in set(snapshot.operation_ids)
        ]
        response = StateTransferResponse(
            request_id=request.request_id,
            checkpoint_id=certificate.checkpoint_id,
            snapshot_id=snapshot.snapshot_id,
            state_hash=snapshot.state_hash,
            height=snapshot.height,
            state=snapshot.state,
            committed_after_checkpoint=committed_after,
        )
        self._event(
            node_id=request.node_id,
            message="state_transfer_response_built",
            details={
                "request_id": request.request_id,
                "checkpoint_id": certificate.checkpoint_id,
                "replay_count": len(committed_after),
                **self._signed_details(
                    self._sign_state_transfer(
                        source_node_id=1,
                        target_node_id=request.node_id,
                        correlation_id=request.request_id,
                        body=response.model_dump(mode="json"),
                    )
                ),
            },
        )
        return response

    def apply_state_transfer(
        self,
        request: StateTransferRequest,
    ) -> RecoveryResult:
        response = self.build_state_transfer_response(request)
        result = RecoveryResult(
            node_id=request.node_id,
            checkpoint_id=response.checkpoint_id,
            snapshot_id=response.snapshot_id,
            applied_state_hash=response.state_hash,
            replayed_operation_ids=response.committed_after_checkpoint,
            status="RECOVERED",
        )
        self.recovery_store.add_recovery(result)
        self.swim_store.mark_alive(request.node_id, reason="state_transfer_applied")
        self._event(
            node_id=request.node_id,
            message="state_transfer_applied",
            details={
                "checkpoint_id": result.checkpoint_id,
                "snapshot_id": result.snapshot_id,
                "replayed_operation_ids": result.replayed_operation_ids,
                "final_node_status": NodeStatus.ALIVE.value,
            },
        )
        return result

    def recover_node(
        self,
        node_id: int,
        checkpoint_id: str | None = None,
        reason: str = "stale_or_crashed_node",
    ) -> RecoveryResult:
        request = self.request_state_transfer(node_id, checkpoint_id, reason)
        return self.apply_state_transfer(request)

    def status(self) -> RecoveryStatus:
        return self.recovery_store.status()

    def clear(self) -> None:
        self.recovery_store.clear()

    def _event(self, node_id: int | None, message: str, details: dict) -> None:
        self.event_log.append(
            ProtocolEvent(
                event_id=str(uuid.uuid4()),
                node_id=node_id,
                protocol=ProtocolName.RECOVERY,
                operation_id=None,
                status=None,
                message=message,
                details=details,
            )
        )

    def _sign_state_transfer(
        self,
        *,
        source_node_id: int,
        target_node_id: int | None,
        correlation_id: str,
        body: dict,
    ):
        if self.crypto_service is None:
            return None
        payload = BftMessagePayload(
            protocol=ProtocolName.RECOVERY,
            message_kind=MessageKind.STATE_TRANSFER,
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
    def _signed_details(message) -> dict:
        if message is None:
            return {}
        return {
            "signed_message_id": message.message_id,
            "signed_message": message.model_dump(mode="json"),
        }
