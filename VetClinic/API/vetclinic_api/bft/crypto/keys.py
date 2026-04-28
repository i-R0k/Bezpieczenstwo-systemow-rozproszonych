from __future__ import annotations

import base64
from datetime import datetime, timezone

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from pydantic import BaseModel, Field


class NodeKeyPair(BaseModel):
    node_id: int
    public_key_b64: str
    private_key_b64: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def generate_node_keypair(node_id: int) -> NodeKeyPair:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return NodeKeyPair(
        node_id=node_id,
        public_key_b64=base64.b64encode(public_bytes).decode("ascii"),
        private_key_b64=base64.b64encode(private_bytes).decode("ascii"),
    )


def sign_bytes(private_key_b64: str, payload: bytes) -> str:
    private_key = Ed25519PrivateKey.from_private_bytes(base64.b64decode(private_key_b64))
    return base64.b64encode(private_key.sign(payload)).decode("ascii")


def verify_bytes(public_key_b64: str, payload: bytes, signature_b64: str) -> bool:
    try:
        public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64))
        public_key.verify(base64.b64decode(signature_b64), payload)
        return True
    except Exception:
        return False
