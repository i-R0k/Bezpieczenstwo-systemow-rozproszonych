from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from vetclinic_api.bft.common.types import MessageKind, ProtocolName
from vetclinic_api.bft.crypto.envelope import BftSignedMessage
from vetclinic_api.bft.fault_injection.models import FaultEvaluationContext


RPC_NAME_BY_PROTOCOL_KIND: dict[tuple[str, str], str] = {
    (ProtocolName.NARWHAL.value, MessageKind.BATCH.value): "SendBatch",
    (ProtocolName.NARWHAL.value, MessageKind.BATCH_ACK.value): "SendBatchAck",
    (ProtocolName.HOTSTUFF.value, MessageKind.PROPOSAL.value): "SendProposal",
    (ProtocolName.HOTSTUFF.value, MessageKind.VOTE.value): "SendVote",
    (ProtocolName.SWIM.value, MessageKind.SWIM_PING.value): "SendSwimPing",
    (ProtocolName.SWIM.value, MessageKind.SWIM_GOSSIP.value): "SendSwimGossip",
    (ProtocolName.RECOVERY.value, MessageKind.STATE_TRANSFER.value): "SendStateTransferRequest",
    (ProtocolName.CHECKPOINTING.value, MessageKind.STATE_TRANSFER.value): "SendStateTransferResponse",
}


def _enum_value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _unix_ms(value: datetime) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return int(value.timestamp() * 1000)


def bft_signed_message_to_grpc_envelope_dict(message: BftSignedMessage) -> dict[str, Any]:
    """Map the in-memory signed envelope to the protobuf BftEnvelope shape."""

    payload = message.payload
    return {
        "message_id": message.message_id,
        "nonce": message.nonce,
        "protocol": _enum_value(payload.protocol),
        "message_kind": _enum_value(payload.message_kind),
        "source_node_id": payload.source_node_id,
        "target_node_id": payload.target_node_id or 0,
        "operation_id": payload.operation_id or "",
        "correlation_id": payload.correlation_id or "",
        "payload_json": json.dumps(payload.body, sort_keys=True, separators=(",", ":")),
        "signature_b64": message.signature_b64,
        "public_key_b64": message.public_key_b64,
        "created_unix_ms": _unix_ms(payload.created_at),
    }


def grpc_envelope_dict_to_fault_context(envelope: dict[str, Any]) -> FaultEvaluationContext:
    """Convert a protobuf-like envelope dictionary to a fault injection context."""

    target_node_id = envelope.get("target_node_id")
    return FaultEvaluationContext(
        protocol=ProtocolName(envelope["protocol"]),
        message_kind=MessageKind(envelope["message_kind"]),
        source_node_id=envelope.get("source_node_id") or None,
        target_node_id=target_node_id or None,
        operation_id=envelope.get("operation_id") or None,
        message_id=envelope.get("message_id") or None,
        metadata={
            "transport": "grpc-contract",
            "correlation_id": envelope.get("correlation_id") or None,
        },
    )


def protocol_message_kind_to_rpc_name(protocol: str | ProtocolName, kind: str | MessageKind) -> str:
    """Return the BftNodeService RPC name for a protocol/message-kind pair."""

    key = (_enum_value(protocol), _enum_value(kind))
    if key not in RPC_NAME_BY_PROTOCOL_KIND:
        raise ValueError(f"No gRPC RPC mapping for protocol={key[0]} kind={key[1]}")
    return RPC_NAME_BY_PROTOCOL_KIND[key]
