from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from vetclinic_api.bft.common.types import MessageKind, ProtocolName
from vetclinic_api.bft.crypto.canonical import canonical_json_bytes


class BftMessagePayload(BaseModel):
    protocol: ProtocolName
    message_kind: MessageKind
    source_node_id: int
    target_node_id: int | None = None
    operation_id: str | None = None
    correlation_id: str | None = None
    body: dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BftSignedMessage(BaseModel):
    message_id: str
    nonce: str
    payload: BftMessagePayload
    signature_b64: str
    public_key_b64: str
    signed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BftVerificationResult(BaseModel):
    valid: bool
    message_id: str | None = None
    replay: bool = False
    reason: str | None = None
    source_node_id: int | None = None


def unsigned_message_material(payload: BftMessagePayload, nonce: str) -> bytes:
    return canonical_json_bytes({"payload": payload, "nonce": nonce})


def compute_message_id(payload: BftMessagePayload, nonce: str) -> str:
    return hashlib.sha256(unsigned_message_material(payload, nonce)).hexdigest()
