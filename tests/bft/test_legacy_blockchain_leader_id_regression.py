from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from vetclinic_api.blockchain.core import (
    InMemoryStorage,
    SQLAlchemyStorage,
    Transaction,
    TxPayload,
    build_block_proposal,
    get_signing_leader_id,
    legacy_block_header_bytes,
    verify_block_signature,
    verify_chain,
)
from vetclinic_api.core.database import Base
from vetclinic_api.crypto.ed25519 import (
    generate_keypair,
    load_leader_keys_from_env,
    sign_message,
)


def _set_leader_keys(monkeypatch, *, leader_id: int = 1, node_id: int = 1) -> tuple[str, str]:
    priv, pub = generate_keypair()
    monkeypatch.setenv("LEADER_ID", str(leader_id))
    monkeypatch.setenv("NODE_ID", str(node_id))
    monkeypatch.setenv("LEADER_PRIV_KEY", priv)
    monkeypatch.setenv("LEADER_PUB_KEY", pub)
    monkeypatch.setenv(f"NODE_{leader_id}_PUB_KEY", pub)
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


def test_get_signing_leader_id_uses_leader_id_not_node_id(monkeypatch) -> None:
    _set_leader_keys(monkeypatch, leader_id=1, node_id=2)

    assert get_signing_leader_id() == 1


def test_block_proposal_uses_signing_leader_id_and_verifies(monkeypatch) -> None:
    _set_leader_keys(monkeypatch, leader_id=1, node_id=2)
    storage = InMemoryStorage()
    storage.add_transaction(_make_transaction())

    proposal = build_block_proposal(storage)
    storage.add_block(proposal.block)

    assert proposal.block.leader_id == 1
    assert verify_block_signature(proposal.block)["ok"] is True

    verification = verify_chain(storage)
    assert verification["verification_status"] == "VALID"
    assert not any(
        "invalid leader_sig" in error.get("reason", "")
        for error in verification.get("errors", [])
    )


def test_block_signed_with_legacy_payload_is_stale_not_invalid(monkeypatch) -> None:
    _set_leader_keys(monkeypatch, leader_id=1, node_id=1)
    storage = InMemoryStorage()
    storage.add_transaction(_make_transaction())
    block = build_block_proposal(storage).block.model_copy()
    keys = load_leader_keys_from_env()
    block.leader_sig = sign_message(keys.priv, legacy_block_header_bytes(block))

    result = verify_block_signature(block)

    assert result["ok"] is False
    assert result["is_stale"] is True
    assert result["reason"] == (
        "stale chain format: leader_sig verifies only with legacy payload; "
        "reset demo chain required"
    )


def test_reset_demo_chain_creates_valid_genesis(monkeypatch) -> None:
    _set_leader_keys(monkeypatch, leader_id=1, node_id=2)
    storage = InMemoryStorage()
    storage.add_transaction(_make_transaction())
    storage.add_block(build_block_proposal(storage).block)

    genesis = storage.reset_demo_chain()
    verification = verify_chain(storage)

    assert genesis.index == 0
    assert verification["verification_status"] == "VALID"
    assert verification["valid"] is True


def test_sqlalchemy_storage_keeps_valid_chain_across_reopen_and_reset(monkeypatch, tmp_path) -> None:
    _set_leader_keys(monkeypatch, leader_id=1, node_id=1)
    engine = create_engine(
        f"sqlite:///{tmp_path / 'chain.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TempSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    storage = SQLAlchemyStorage(session_factory=TempSession)
    storage.add_transaction(_make_transaction())
    proposal = build_block_proposal(storage)
    storage.add_block(proposal.block)

    assert verify_chain(storage)["verification_status"] == "VALID"

    reopened = SQLAlchemyStorage(session_factory=TempSession)
    assert verify_chain(reopened)["verification_status"] == "VALID"

    reopened.reset_demo_chain()
    reset_verification = verify_chain(reopened)
    assert reset_verification["verification_status"] == "VALID"
    assert reset_verification["valid"] is True
