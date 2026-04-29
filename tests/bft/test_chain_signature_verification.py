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
    assert not any("invalid leader_sig" in reason for reason in reasons)
