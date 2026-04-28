from __future__ import annotations

import uuid

from vetclinic_api.bft.common.events import EVENT_LOG, EventLog, ProtocolEvent
from vetclinic_api.bft.common.types import MessageKind, ProtocolName
from vetclinic_api.bft.crypto.envelope import (
    BftMessagePayload,
    BftSignedMessage,
    BftVerificationResult,
    compute_message_id,
    unsigned_message_material,
)
from vetclinic_api.bft.crypto.keys import NodeKeyPair, sign_bytes, verify_bytes
from vetclinic_api.bft.crypto.registry import (
    NODE_KEY_REGISTRY,
    InMemoryNodeKeyRegistry,
)
from vetclinic_api.bft.fault_injection.replay import REPLAY_GUARD, ReplayGuard


class CryptoService:
    def __init__(
        self,
        key_registry: InMemoryNodeKeyRegistry,
        replay_guard: ReplayGuard,
        event_log: EventLog,
    ) -> None:
        self.key_registry = key_registry
        self.replay_guard = replay_guard
        self.event_log = event_log

    def ensure_demo_keys(self, total_nodes: int) -> list[NodeKeyPair]:
        if total_nodes <= 0:
            raise ValueError("total_nodes must be greater than 0")
        return self.key_registry.ensure_demo_keys(list(range(1, total_nodes + 1)))

    def sign_message(
        self,
        payload: BftMessagePayload,
        source_node_id: int,
    ) -> BftSignedMessage:
        private_key = self.key_registry.get_private_key(source_node_id)
        public_key = self.key_registry.get_public_key(source_node_id)
        nonce = str(uuid.uuid4())
        message_id = compute_message_id(payload, nonce)
        signature = sign_bytes(private_key, unsigned_message_material(payload, nonce))
        message = BftSignedMessage(
            message_id=message_id,
            nonce=nonce,
            payload=payload,
            signature_b64=signature,
            public_key_b64=public_key,
        )
        self._event(
            payload.protocol,
            payload.source_node_id,
            "bft_message_signed",
            {
                "message_id": message.message_id,
                "message_kind": payload.message_kind.value,
                "target_node_id": payload.target_node_id,
            },
        )
        return message

    def verify_message(
        self,
        message: BftSignedMessage,
        mark_seen: bool = True,
    ) -> BftVerificationResult:
        source = message.payload.source_node_id
        try:
            expected_public_key = self.key_registry.get_public_key(source)
        except KeyError:
            return self._rejected(message, "unknown_public_key")

        if expected_public_key != message.public_key_b64:
            return self._rejected(message, "public_key_mismatch")

        expected_message_id = compute_message_id(message.payload, message.nonce)
        if expected_message_id != message.message_id:
            return self._rejected(message, "message_id_mismatch")

        if not verify_bytes(
            message.public_key_b64,
            unsigned_message_material(message.payload, message.nonce),
            message.signature_b64,
        ):
            return self._rejected(message, "invalid_signature")

        if mark_seen and self.replay_guard.check_and_mark(message.message_id):
            result = BftVerificationResult(
                valid=False,
                message_id=message.message_id,
                replay=True,
                reason="replay_detected",
                source_node_id=source,
            )
            self._event(
                message.payload.protocol,
                source,
                "bft_message_rejected",
                {"message_id": message.message_id, "reason": result.reason},
            )
            return result

        result = BftVerificationResult(
            valid=True,
            message_id=message.message_id,
            replay=False,
            reason=None,
            source_node_id=source,
        )
        self._event(
            message.payload.protocol,
            source,
            "bft_message_verified",
            {
                "message_id": message.message_id,
                "message_kind": message.payload.message_kind.value,
            },
        )
        return result

    def verify_message_for_protocol(
        self,
        message: BftSignedMessage,
        expected_protocol: ProtocolName,
        expected_kind: MessageKind | None = None,
    ) -> BftVerificationResult:
        if message.payload.protocol != expected_protocol:
            return self._rejected(message, "protocol_mismatch")
        if expected_kind is not None and message.payload.message_kind != expected_kind:
            return self._rejected(message, "message_kind_mismatch")
        return self.verify_message(message)

    def clear(self) -> None:
        self.key_registry.clear()
        self.replay_guard.clear()

    def _rejected(
        self,
        message: BftSignedMessage,
        reason: str,
    ) -> BftVerificationResult:
        result = BftVerificationResult(
            valid=False,
            message_id=message.message_id,
            replay=False,
            reason=reason,
            source_node_id=message.payload.source_node_id,
        )
        self._event(
            message.payload.protocol,
            message.payload.source_node_id,
            "bft_message_rejected",
            {"message_id": message.message_id, "reason": reason},
        )
        return result

    def _event(
        self,
        protocol: ProtocolName,
        node_id: int,
        message: str,
        details: dict,
    ) -> None:
        self.event_log.append(
            ProtocolEvent(
                event_id=str(uuid.uuid4()),
                node_id=node_id,
                protocol=protocol,
                operation_id=None,
                status=None,
                message=message,
                details=details,
            )
        )


CRYPTO_SERVICE = CryptoService(NODE_KEY_REGISTRY, REPLAY_GUARD, EVENT_LOG)
