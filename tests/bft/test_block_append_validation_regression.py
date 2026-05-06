from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from vetclinic_api.blockchain.core import (
    InMemoryStorage,
    SQLAlchemyStorage,
    Transaction,
    TxPayload,
    build_block_proposal,
    verify_block_signature,
)
from vetclinic_api.core.database import Base
from vetclinic_api.crypto.ed25519 import generate_keypair, load_leader_keys_from_env, sign_message


def _set_leader_keys(monkeypatch, leader_id: int = 1) -> None:
    priv, pub = generate_keypair()
    monkeypatch.setenv("LEADER_ID", str(leader_id))
    monkeypatch.setenv("NODE_ID", str(leader_id))
    monkeypatch.setenv("LEADER_PRIV_KEY", priv)
    monkeypatch.setenv("LEADER_PUB_KEY", pub)
    monkeypatch.delenv(f"NODE_{leader_id}_PUB_KEY", raising=False)


def _make_transaction() -> Transaction:
    payload = TxPayload(sender="alice", recipient="bob", amount=Decimal("1.23"))
    timestamp = datetime.utcnow()
    raw = json.dumps(
        {"payload": payload.model_dump(mode="json"), "timestamp": timestamp.isoformat()},
        sort_keys=True,
    ).encode("utf-8")
    return Transaction(
        id=hashlib.sha256(raw).hexdigest(),
        payload=payload,
        sender_pub="demo-sender-pub",
        signature=sign_message(load_leader_keys_from_env().priv, raw),
        timestamp=timestamp,
    )


def test_build_block_proposal_verifies_immediately_and_after_json_roundtrip(monkeypatch) -> None:
    _set_leader_keys(monkeypatch)
    storage = InMemoryStorage()
    storage.add_transaction(_make_transaction())

    proposal = build_block_proposal(storage)
    roundtripped = type(proposal.block).model_validate_json(
        proposal.block.model_dump_json(),
    )

    assert verify_block_signature(proposal.block)["ok"] is True
    assert verify_block_signature(roundtripped)["ok"] is True


def test_sqlalchemy_roundtrip_keeps_block_signature_valid(monkeypatch, tmp_path) -> None:
    _set_leader_keys(monkeypatch)
    engine = create_engine(
        f"sqlite:///{tmp_path / 'chain.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    storage = SQLAlchemyStorage(session_factory=session_factory)
    storage.add_transaction(_make_transaction())
    proposal = build_block_proposal(storage)
    storage.add_block(proposal.block)

    reopened = SQLAlchemyStorage(session_factory=session_factory)
    block = reopened.get_chain()[1]

    assert verify_block_signature(block)["ok"] is True


def test_storage_rejects_tampered_leader_signature(monkeypatch) -> None:
    _set_leader_keys(monkeypatch)
    storage = InMemoryStorage()
    storage.add_transaction(_make_transaction())
    block = build_block_proposal(storage).block
    block.leader_sig = "tampered"

    with pytest.raises(ValueError, match="invalid leader_sig"):
        storage.add_block(block)


def test_wrong_current_public_key_returns_deterministic_invalid_leader_sig(monkeypatch) -> None:
    _set_leader_keys(monkeypatch)
    storage = InMemoryStorage()
    storage.add_transaction(_make_transaction())
    block = build_block_proposal(storage).block
    _, wrong_pub = generate_keypair()
    monkeypatch.setenv("NODE_1_PUB_KEY", wrong_pub)

    result = verify_block_signature(block)

    assert result["ok"] is False
    assert result["reason"] == "invalid leader_sig for leader_id=1"
