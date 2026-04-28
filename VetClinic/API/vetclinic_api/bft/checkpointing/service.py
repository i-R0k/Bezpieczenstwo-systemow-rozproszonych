from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from vetclinic_api.bft.checkpointing.models import (
    CheckpointCertificate,
    CheckpointStatus,
    StateSnapshot,
)
from vetclinic_api.bft.checkpointing.store import InMemoryCheckpointStore
from vetclinic_api.bft.common.events import EventLog, ProtocolEvent
from vetclinic_api.bft.common.operations import InMemoryOperationStore
from vetclinic_api.bft.common.quorum import quorum_size
from vetclinic_api.bft.common.types import MessageKind, OperationStatus, ProtocolName
from vetclinic_api.bft.crypto.envelope import BftMessagePayload
from vetclinic_api.bft.crypto.service import CryptoService


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class CheckpointService:
    def __init__(
        self,
        operation_store: InMemoryOperationStore,
        checkpoint_store: InMemoryCheckpointStore,
        event_log: EventLog,
        crypto_service: CryptoService | None = None,
    ) -> None:
        self.operation_store = operation_store
        self.checkpoint_store = checkpoint_store
        self.event_log = event_log
        self.crypto_service = crypto_service

    def create_snapshot(self, node_id: int) -> StateSnapshot:
        committed = [
            operation
            for operation in self.operation_store.list(limit=10000)
            if operation.status in {OperationStatus.COMMITTED, OperationStatus.EXECUTED}
        ]
        committed = sorted(committed, key=lambda operation: operation.created_at.isoformat())
        state = {
            "operations": [
                {
                    "operation_id": operation.operation_id,
                    "sender": operation.sender,
                    "recipient": operation.recipient,
                    "amount": operation.amount,
                    "payload": operation.payload,
                    "status": operation.status.value,
                }
                for operation in committed
            ]
        }
        state_hash = stable_hash(state)
        snapshot = StateSnapshot(
            snapshot_id=stable_hash(
                {
                    "node_id": node_id,
                    "height": len(committed),
                    "state_hash": state_hash,
                }
            ),
            node_id=node_id,
            height=len(committed),
            operation_ids=[operation.operation_id for operation in committed],
            state=state,
            state_hash=state_hash,
        )
        self.checkpoint_store.add_snapshot(snapshot)
        self._event(
            node_id=node_id,
            message="checkpoint_snapshot_created",
            details={
                "snapshot_id": snapshot.snapshot_id,
                "height": snapshot.height,
                "state_hash": snapshot.state_hash,
            },
        )
        return snapshot

    def certify_snapshot(
        self,
        snapshot_id: str,
        total_nodes: int,
        signer_node_ids: list[int] | None = None,
    ) -> CheckpointCertificate:
        snapshot = self.checkpoint_store.get_snapshot(snapshot_id)
        required = quorum_size(total_nodes)
        signers = sorted(set(signer_node_ids or range(1, total_nodes + 1)))
        if len(signers) < required:
            raise ValueError("Not enough checkpoint signers for quorum")
        certificate = CheckpointCertificate(
            checkpoint_id=stable_hash(
                {
                    "snapshot_id": snapshot.snapshot_id,
                    "state_hash": snapshot.state_hash,
                    "signer_node_ids": signers[:required],
                }
            ),
            snapshot_id=snapshot.snapshot_id,
            state_hash=snapshot.state_hash,
            height=snapshot.height,
            signer_node_ids=signers[:required],
            quorum_size=required,
            total_nodes=total_nodes,
            valid=True,
        )
        signed_messages = []
        for signer in certificate.signer_node_ids:
            signed = self._sign_checkpoint_vote(signer, certificate)
            if signed:
                signed_messages.append(signed)
        self.checkpoint_store.add_certificate(certificate)
        self._event(
            node_id=snapshot.node_id,
            message="checkpoint_certificate_formed",
            details={
                "checkpoint_id": certificate.checkpoint_id,
                "snapshot_id": snapshot.snapshot_id,
                "signer_node_ids": certificate.signer_node_ids,
                "signed_message_ids": [message.message_id for message in signed_messages],
                "signed_messages": [
                    message.model_dump(mode="json") for message in signed_messages
                ],
            },
        )
        return certificate

    def status(self) -> CheckpointStatus:
        return self.checkpoint_store.status()

    def clear(self) -> None:
        self.checkpoint_store.clear()

    def _event(self, node_id: int | None, message: str, details: dict) -> None:
        self.event_log.append(
            ProtocolEvent(
                event_id=str(uuid.uuid4()),
                node_id=node_id,
                protocol=ProtocolName.CHECKPOINTING,
                operation_id=None,
                status=None,
                message=message,
                details=details,
            )
        )

    def _sign_checkpoint_vote(
        self,
        signer_node_id: int,
        certificate: CheckpointCertificate,
    ):
        if self.crypto_service is None:
            return None
        payload = BftMessagePayload(
            protocol=ProtocolName.CHECKPOINTING,
            message_kind=MessageKind.CHECKPOINT,
            source_node_id=signer_node_id,
            target_node_id=None,
            operation_id=None,
            correlation_id=certificate.checkpoint_id,
            body={
                "checkpoint_id": certificate.checkpoint_id,
                "snapshot_id": certificate.snapshot_id,
                "state_hash": certificate.state_hash,
                "height": certificate.height,
            },
        )
        try:
            return self.crypto_service.sign_message(payload, signer_node_id)
        except KeyError:
            self.crypto_service.key_registry.ensure_demo_keys([signer_node_id])
            return self.crypto_service.sign_message(payload, signer_node_id)
