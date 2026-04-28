from __future__ import annotations

from vetclinic_api.bft.common.types import MessageKind, ProtocolName
from vetclinic_api.bft.crypto.canonical import canonical_json_bytes
from vetclinic_api.bft.crypto.envelope import (
    BftMessagePayload,
    compute_message_id,
    unsigned_message_material,
)
from vetclinic_api.bft.crypto.keys import generate_node_keypair, sign_bytes, verify_bytes


def _payload(body):
    return BftMessagePayload(
        protocol=ProtocolName.HOTSTUFF,
        message_kind=MessageKind.VOTE,
        source_node_id=1,
        body=body,
    )


def test_canonical_json_and_message_id_are_deterministic():
    assert canonical_json_bytes({"b": 2, "a": 1}) == canonical_json_bytes({"a": 1, "b": 2})
    payload = _payload({"value": 1})
    assert compute_message_id(payload, "nonce") == compute_message_id(payload, "nonce")
    assert compute_message_id(payload, "nonce") != compute_message_id(_payload({"value": 2}), "nonce")


def test_signature_covers_nonce_and_body():
    keypair = generate_node_keypair(1)
    payload = _payload({"value": 1})
    signature = sign_bytes(keypair.private_key_b64, unsigned_message_material(payload, "n1"))
    assert verify_bytes(keypair.public_key_b64, unsigned_message_material(payload, "n1"), signature)
    assert not verify_bytes(keypair.public_key_b64, unsigned_message_material(payload, "n2"), signature)
    assert not verify_bytes(keypair.public_key_b64, unsigned_message_material(_payload({"value": 2}), "n1"), signature)
