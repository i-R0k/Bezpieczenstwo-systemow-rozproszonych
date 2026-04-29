from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal

from vetclinic_api.blockchain.core import (
    InMemoryStorage,
    Transaction,
    TxPayload,
    build_block_proposal,
    build_canonical_block_payload,
    verify_block_signature,
    verify_chain,
)
from vetclinic_api.crypto.ed25519 import generate_keypair, load_leader_keys_from_env, sign_message


def _set_leader_keys(monkeypatch, leader_id: int = 1) -> tuple[str, str]:
    priv, pub = generate_keypair()
    monkeypatch.setenv("LEADER_ID", str(leader_id))
    monkeypatch.setenv("NODE_ID", str(leader_id))
    monkeypatch.setenv("LEADER_PRIV_KEY", priv)
    monkeypatch.setenv("LEADER_PUB_KEY", pub)
    monkeypatch.delenv(f"NODE_{leader_id}_PUB_KEY", raising=False)
    return priv, pub


def _make_transaction() -> Transaction:
    payload = TxPayload(sender="alice", recipient="bob", amount=Decimal("1.0"))
    timestamp = datetime.utcnow()
    raw = json.dumps(
        {"payload": payload.model_dump(mode="json"), "timestamp": timestamp.isoformat()},
        sort_keys=True,
    ).encode("utf-8")
    tx_id = hashlib.sha256(raw).hexdigest()
    keys = load_leader_keys_from_env()
    return Transaction(
        id=tx_id,
        payload=payload,
        sender_pub="demo-sender-pub",
        signature=sign_message(keys.priv, raw),
        timestamp=timestamp,
    )


def _build_demo_chain() -> InMemoryStorage:
    storage = InMemoryStorage()
    storage.add_transaction(_make_transaction())
    proposal = build_block_proposal(storage)
    storage.add_block(proposal.block)
    return storage


def test_block_signed_by_its_leader_verifies(monkeypatch) -> None:
    _set_leader_keys(monkeypatch, leader_id=1)
    storage = _build_demo_chain()

    block = storage.get_chain()[1]
    result = verify_block_signature(block)

    assert result["ok"] is True
    assert result["leader_id"] == 1
    assert verify_chain(storage)["valid"] is True


def test_signing_payload_does_not_include_leader_signature(monkeypatch) -> None:
    _set_leader_keys(monkeypatch, leader_id=1)
    storage = _build_demo_chain()
    block = storage.get_chain()[1]

    payload = build_canonical_block_payload(block)

    assert b"leader_sig" not in payload
    assert b"valid" not in payload
    assert b"faults" not in payload


def test_block_verified_with_wrong_node_key_fails(monkeypatch) -> None:
    _set_leader_keys(monkeypatch, leader_id=1)
    _, wrong_pub = generate_keypair()
    monkeypatch.setenv("NODE_1_PUB_KEY", wrong_pub)
    storage = _build_demo_chain()

    result = verify_block_signature(storage.get_chain()[1])

    assert result["ok"] is False
    assert result["reason"] == "invalid leader_sig for leader_id=1"


def test_missing_leader_id_returns_controlled_stale_format_error(monkeypatch) -> None:
    _set_leader_keys(monkeypatch, leader_id=1)
    storage = _build_demo_chain()
    block = storage.get_chain()[1].model_copy()
    block.leader_id = None

    result = verify_block_signature(block)

    assert result["ok"] is False
    assert result["reason"] == "stale chain format: missing leader_id"
    assert result.get("is_stale") is True
    storage._chain[1] = block
    chain_result = verify_chain(storage)
    assert chain_result["verification_status"] == "STALE"
    assert chain_result["valid"] is None


def test_tampered_canonical_payload_fails_signature(monkeypatch) -> None:
    _set_leader_keys(monkeypatch, leader_id=1)
    storage = _build_demo_chain()
    block = storage.get_chain()[1].model_copy()
    block.nonce += 1

    result = verify_block_signature(block)

    assert result["ok"] is False
    assert "invalid leader_sig" in result["reason"]


def test_network_regression_valid_chain_has_no_invalid_leader_sig(monkeypatch) -> None:
    _set_leader_keys(monkeypatch, leader_id=1)
    storage = _build_demo_chain()

    result = verify_chain(storage)
    reasons = [error["reason"] for error in result["errors"]]

    assert result["valid"] is True
    assert result["verification_status"] == "VALID"
    assert not any("invalid leader_sig" in reason for reason in reasons)


def test_reset_demo_chain_creates_valid_genesis_state(monkeypatch) -> None:
    _set_leader_keys(monkeypatch, leader_id=1)
    storage = _build_demo_chain()
    assert storage.get_chain()[-1].index == 1

    genesis = storage.reset_demo_chain()
    result = verify_chain(storage)

    assert genesis.index == 0
    assert result["verification_status"] == "VALID"
    assert result["valid"] is True
    assert len(storage.get_chain()) == 1


def test_block_without_signature_but_with_leader_id_is_invalid_not_stale(monkeypatch) -> None:
    """Nowy format (ma leader_id) ale brak podpisu -> INVALID, nie STALE."""
    _set_leader_keys(monkeypatch, leader_id=1)
    storage = _build_demo_chain()
    block = storage.get_chain()[1].model_copy()
    block.leader_sig = ""

    result = verify_block_signature(block)

    assert result["ok"] is False
    assert result["reason"] == "missing leader_sig"
    assert result.get("is_stale") is False
    
    storage._chain[1] = block
    chain_result = verify_chain(storage)
    # Blok nowego formatu bez podpisu -> INVALID, nie STALE
    assert chain_result["verification_status"] == "INVALID"
    assert chain_result["valid"] is False
