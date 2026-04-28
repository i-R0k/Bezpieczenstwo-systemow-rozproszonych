from __future__ import annotations

import uuid

from vetclinic_api.bft.common.events import EventLog, ProtocolEvent
from vetclinic_api.bft.common.operations import InMemoryOperationStore
from vetclinic_api.bft.common.types import MessageKind, OperationStatus, ProtocolName
from vetclinic_api.bft.crypto.envelope import BftMessagePayload
from vetclinic_api.bft.crypto.service import CryptoService
from vetclinic_api.bft.fault_injection.models import FaultEvaluationContext
from vetclinic_api.bft.fault_injection.service import FaultInjectionService
from vetclinic_api.bft.narwhal.models import (
    BatchAck,
    BatchCertificate,
    NarwhalBatchResponse,
    NarwhalDagView,
)
from vetclinic_api.bft.narwhal.store import InMemoryNarwhalStore


class NarwhalService:
    def __init__(
        self,
        operation_store: InMemoryOperationStore,
        event_log: EventLog,
        narwhal_store: InMemoryNarwhalStore,
        fault_service: FaultInjectionService | None = None,
        crypto_service: CryptoService | None = None,
    ) -> None:
        self.operation_store = operation_store
        self.event_log = event_log
        self.narwhal_store = narwhal_store
        self.fault_service = fault_service
        self.crypto_service = crypto_service

    def create_batch_from_operations(
        self,
        author_node_id: int,
        total_nodes: int,
        operation_ids: list[str] | None,
        max_operations: int,
    ) -> NarwhalBatchResponse:
        self.narwhal_store.set_total_nodes(total_nodes)
        selected_ids = self._select_operation_ids(operation_ids, max_operations)
        if not selected_ids:
            raise ValueError("No RECEIVED operations available for batching")

        operations = [self.operation_store.get(operation_id) for operation_id in selected_ids]
        not_received = [
            operation.operation_id
            for operation in operations
            if operation.status != OperationStatus.RECEIVED
        ]
        if not_received:
            raise ValueError(
                f"Operations are not RECEIVED and cannot be batched: {not_received}"
            )

        batch_decision = self._evaluate_fault(
            message_kind=MessageKind.BATCH,
            source_node_id=author_node_id,
            target_node_id=None,
            operation_id=selected_ids[0] if len(selected_ids) == 1 else None,
            message_id=None,
            metadata={"operation_ids": selected_ids},
        )
        if batch_decision and (batch_decision.should_drop or batch_decision.blocked_by_partition):
            self._append_event(
                node_id=author_node_id,
                operation_id=selected_ids[0] if len(selected_ids) == 1 else None,
                status=None,
                message="narwhal_batch_dropped",
                details={
                    "operation_ids": selected_ids,
                    "blocked_by_partition": batch_decision.blocked_by_partition,
                },
            )
            raise ValueError("Narwhal batch blocked by fault injection")

        batch = self.narwhal_store.create_batch(
            author_node_id=author_node_id,
            round=self.narwhal_store.next_round(),
            operation_ids=selected_ids,
            parent_batch_ids=self.narwhal_store.get_tips(),
        )
        operations_marked: list[str] = []
        for operation_id in selected_ids:
            self.operation_store.transition(
                operation_id=operation_id,
                to_status=OperationStatus.BATCHED,
                protocol=ProtocolName.NARWHAL,
                message="Operation included in Narwhal batch",
                node_id=author_node_id,
                details={"batch_id": batch.batch_id},
            )
            operations_marked.append(operation_id)

        self._append_event(
            node_id=author_node_id,
            operation_id=None,
            status=OperationStatus.BATCHED,
            message="batch_created",
            details={
                "batch_id": batch.batch_id,
                "operation_ids": selected_ids,
                "parent_batch_ids": batch.parent_batch_ids,
                "round": batch.round,
            },
        )
        post_batch_decision = self._evaluate_fault(
            message_kind=MessageKind.BATCH,
            source_node_id=author_node_id,
            target_node_id=None,
            operation_id=selected_ids[0] if len(selected_ids) == 1 else None,
            message_id=batch.batch_id,
            metadata={"batch_id": batch.batch_id},
        )
        if post_batch_decision and post_batch_decision.should_duplicate:
            self._append_event(
                node_id=author_node_id,
                operation_id=None,
                status=None,
                message="batch_duplicate_simulated",
                details={"batch_id": batch.batch_id},
            )
        if post_batch_decision and post_batch_decision.should_delay:
            self._append_event(
                node_id=author_node_id,
                operation_id=None,
                status=None,
                message="batch_delay_simulated",
                details={
                    "batch_id": batch.batch_id,
                    "delay_ms": post_batch_decision.delay_ms,
                },
            )
        signed_batch = self._sign_protocol_message(
            source_node_id=author_node_id,
            target_node_id=None,
            message_kind=MessageKind.BATCH,
            operation_id=selected_ids[0] if len(selected_ids) == 1 else None,
            correlation_id=batch.batch_id,
            body={
                "batch_id": batch.batch_id,
                "round": batch.round,
                "operation_ids": selected_ids,
                "payload_hash": batch.payload_hash,
            },
        )
        signed_details = (
            {
                "signed_message_id": signed_batch.message_id,
                "signed_message": signed_batch.model_dump(mode="json"),
            }
            if signed_batch
            else {}
        )

        certificate = self.acknowledge_batch(
            batch_id=batch.batch_id,
            node_id=author_node_id,
            accepted=True,
            reason="author local availability ACK",
            total_nodes=total_nodes,
        )
        if signed_details:
            self._append_event(
                node_id=author_node_id,
                operation_id=None,
                status=None,
                message="narwhal_batch_signed",
                details={"batch_id": batch.batch_id, **signed_details},
            )
        return NarwhalBatchResponse(
            batch=batch,
            certificate=certificate,
            operations_marked=operations_marked,
        )

    def acknowledge_batch(
        self,
        batch_id: str,
        node_id: int,
        accepted: bool = True,
        reason: str | None = None,
        total_nodes: int | None = None,
    ) -> BatchCertificate | None:
        if total_nodes is not None:
            self.narwhal_store.set_total_nodes(total_nodes)

        batch = self.narwhal_store.get_batch(batch_id)
        ack_decision = self._evaluate_fault(
            message_kind=MessageKind.BATCH_ACK,
            source_node_id=node_id,
            target_node_id=batch.author_node_id,
            operation_id=None,
            message_id=f"{batch_id}:ack:{node_id}",
            metadata={"batch_id": batch_id, "accepted": accepted},
        )
        if ack_decision and (ack_decision.should_drop or ack_decision.blocked_by_partition):
            self._append_event(
                node_id=node_id,
                operation_id=None,
                status=None,
                message="narwhal_ack_dropped",
                details={
                    "batch_id": batch_id,
                    "blocked_by_partition": ack_decision.blocked_by_partition,
                },
            )
            return None

        existing_certificate = self.narwhal_store.get_certificate(batch_id)
        ack = BatchAck(
            batch_id=batch_id,
            node_id=node_id,
            accepted=accepted,
            reason=reason,
        )
        signed_ack = self._sign_protocol_message(
            source_node_id=node_id,
            target_node_id=batch.author_node_id,
            message_kind=MessageKind.BATCH_ACK,
            operation_id=None,
            correlation_id=batch_id,
            body={
                "batch_id": batch_id,
                "node_id": node_id,
                "accepted": accepted,
                "reason": reason,
            },
        )
        certificate = self.narwhal_store.add_ack(ack)
        self._append_event(
            node_id=node_id,
            operation_id=None,
            status=None,
            message="batch_acknowledged",
            details={
                "batch_id": batch_id,
                "accepted": accepted,
                "reason": reason,
                **(
                    {
                        "signed_message_id": signed_ack.message_id,
                        "signed_message": signed_ack.model_dump(mode="json"),
                    }
                    if signed_ack
                    else {}
                ),
            },
        )
        if certificate and certificate.available:
            if existing_certificate is None:
                self._mark_batch_available(batch_id, certificate)
        return certificate

    def _evaluate_fault(
        self,
        *,
        message_kind: MessageKind,
        source_node_id: int | None,
        target_node_id: int | None,
        operation_id: str | None,
        message_id: str | None,
        metadata: dict,
    ):
        if self.fault_service is None:
            return None
        return self.fault_service.evaluate(
            FaultEvaluationContext(
                protocol=ProtocolName.NARWHAL,
                message_kind=message_kind,
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                operation_id=operation_id,
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
        operation_id: str | None,
        correlation_id: str | None,
        body: dict,
    ):
        if self.crypto_service is None:
            return None
        payload = BftMessagePayload(
            protocol=ProtocolName.NARWHAL,
            message_kind=message_kind,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            operation_id=operation_id,
            correlation_id=correlation_id,
            body=body,
        )
        try:
            return self.crypto_service.sign_message(payload, source_node_id)
        except KeyError:
            self.crypto_service.key_registry.ensure_demo_keys([source_node_id])
            return self.crypto_service.sign_message(payload, source_node_id)

    def certify_batch_locally(
        self,
        batch_id: str,
        total_nodes: int,
    ) -> BatchCertificate | None:
        self.narwhal_store.set_total_nodes(total_nodes)
        certificate = self.narwhal_store.get_certificate(batch_id)
        if certificate:
            self._mark_batch_available(batch_id, certificate)
            return certificate

        for node_id in range(1, total_nodes + 1):
            certificate = self.acknowledge_batch(
                batch_id=batch_id,
                node_id=node_id,
                accepted=True,
                reason="certify-demo local ACK",
                total_nodes=total_nodes,
            )
            if certificate:
                return certificate
        return certificate

    def get_dag(self) -> NarwhalDagView:
        return self.narwhal_store.get_dag()

    def clear(self) -> None:
        self.narwhal_store.clear()

    def _select_operation_ids(
        self,
        operation_ids: list[str] | None,
        max_operations: int,
    ) -> list[str]:
        if max_operations <= 0:
            raise ValueError("max_operations must be greater than 0")
        if operation_ids is not None:
            return list(operation_ids)

        return [
            operation.operation_id
            for operation in self.operation_store.list(limit=10000)
            if operation.status == OperationStatus.RECEIVED
        ][:max_operations]

    def _mark_batch_available(
        self,
        batch_id: str,
        certificate: BatchCertificate,
    ) -> None:
        batch = self.narwhal_store.get_batch(batch_id)
        newly_available: list[str] = []
        for operation_id in batch.operation_ids:
            operation = self.operation_store.get(operation_id)
            if operation.status == OperationStatus.BATCHED:
                self.operation_store.transition(
                    operation_id=operation_id,
                    to_status=OperationStatus.AVAILABLE,
                    protocol=ProtocolName.NARWHAL,
                    message="Operation made available by Narwhal certificate",
                    node_id=None,
                    details={"batch_id": batch_id},
                )
                newly_available.append(operation_id)
                self._append_event(
                    node_id=None,
                    operation_id=operation_id,
                    status=OperationStatus.AVAILABLE,
                    message="operation_available",
                    details={"batch_id": batch_id},
                )

        self._append_event(
            node_id=None,
            operation_id=None,
            status=OperationStatus.AVAILABLE,
            message="batch_certified",
            details={
                "batch_id": batch_id,
                "ack_node_ids": certificate.ack_node_ids,
                "quorum_size": certificate.quorum_size,
                "total_nodes": certificate.total_nodes,
                "operations_marked": newly_available,
            },
        )

    def _append_event(
        self,
        *,
        node_id: int | None,
        operation_id: str | None,
        status: OperationStatus | None,
        message: str,
        details: dict,
    ) -> None:
        self.event_log.append(
            ProtocolEvent(
                event_id=str(uuid.uuid4()),
                node_id=node_id,
                protocol=ProtocolName.NARWHAL,
                operation_id=operation_id,
                status=status,
                message=message,
                details=details,
            )
        )
