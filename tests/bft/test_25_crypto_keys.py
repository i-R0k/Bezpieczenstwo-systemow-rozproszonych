from __future__ import annotations

from vetclinic_api.bft.crypto.keys import generate_node_keypair, sign_bytes, verify_bytes


def test_node_keypair_sign_verify_and_registry(node_key_registry):
    keypair = generate_node_keypair(1)
    assert keypair.public_key_b64
    assert keypair.private_key_b64
    signature = sign_bytes(keypair.private_key_b64, b"payload")
    assert verify_bytes(keypair.public_key_b64, b"payload", signature) is True
    assert verify_bytes(keypair.public_key_b64, b"changed", signature) is False
    assert verify_bytes(keypair.public_key_b64, b"payload", "bad") is False

    node_key_registry.register_keypair(keypair)
    assert node_key_registry.get_public_key(1) == keypair.public_key_b64
    assert node_key_registry.get_private_key(1) == keypair.private_key_b64
    public_before = node_key_registry.get_public_key(1)
    node_key_registry.ensure_demo_keys([1, 2])
    assert node_key_registry.get_public_key(1) == public_before
    assert 2 in node_key_registry.public_keys()
    assert keypair.private_key_b64 not in str(node_key_registry.public_keys())
