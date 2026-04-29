"""
Test regresji: zakładka Sieć nie powinna pokazywać "invalid leader_sig" dla świeżego demo chain.

Problem: https://github.com/i-R0k/Bezpieczenstwo-systemow-rozproszonych
- Node'y pokazywały INVALID z "invalid leader_sig" nawet dla nowych bloków
- Root cause: brak NODE_1_PUB_KEY w docker-compose + stare bloki bez leader_id

Sprawdzenia:
1. Nowy chain (po reset) ma wszystkie bloki VALID
2. Bloki bez leader_id (legacy format) są oznaczane jako STALE, nie INVALID
3. Świeże bloki z leader_id i prawidłowym podpisem nie mają fault'ów
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from VetClinic.API.vetclinic_api.blockchain.core import (
    InMemoryStorage,
    Transaction,
    TxPayload,
    build_block_proposal,
    verify_chain,
    verify_block_signature,
)
from VetClinic.API.vetclinic_api.crypto.ed25519 import generate_keypair, load_leader_keys_from_env, sign_message


def _set_leader_keys(monkeypatch, leader_id: int = 1) -> tuple[str, str]:
    priv, pub = generate_keypair()
    monkeypatch.setenv("LEADER_ID", str(leader_id))
    monkeypatch.setenv("NODE_ID", str(leader_id))
    monkeypatch.setenv("LEADER_PRIV_KEY", priv)
    monkeypatch.setenv("LEADER_PUB_KEY", pub)
    monkeypatch.setenv(f"NODE_{leader_id}_PUB_KEY", pub)
    return priv, pub


def _make_transaction() -> Transaction:
    payload = TxPayload(sender="alice", recipient="bob", amount=Decimal("1.0"))
    timestamp = datetime.utcnow()
    import hashlib
    import json
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


def test_network_tab_fresh_chain_has_no_invalid_leader_sig(monkeypatch) -> None:
    """
    Test regresji: świeży chain nie powinien mieć 'invalid leader_sig'.
    
    Scenariusz:
    1. Reset demo chain (genesis)
    2. Dodaj i pomineej blok
    3. Weryfikuj, że verification_status == VALID
    4. Sprawdź, że żaden error nie zawiera 'invalid leader_sig'
    """
    _set_leader_keys(monkeypatch, leader_id=1)
    
    # Stwórz świeży chain
    storage = InMemoryStorage()
    
    # Dodaj jeden blok
    storage.add_transaction(_make_transaction())
    proposal = build_block_proposal(storage)
    storage.add_block(proposal.block)
    
    # Weryfikuj cały chain
    result = verify_chain(storage)
    
    # Sprawdzenia
    assert result["verification_status"] == "VALID", f"Expected VALID, got {result['verification_status']}"
    assert result["valid"] is True, f"Expected valid=True, got {result['valid']}"
    
    errors = result.get("errors", [])
    for error in errors:
        reason = error.get("reason", "")
        assert "invalid leader_sig" not in reason, (
            f"Fresh chain should not have 'invalid leader_sig' errors. "
            f"Found: {reason}"
        )


def test_stale_chain_format_is_not_masked_as_regular_invalid(monkeypatch) -> None:
    """
    Test: stary format (brak leader_id) powinien być STALE, nie INVALID.
    
    Ważne: jeśli użytkownik widzi STALE, wie że musi zrobić Reset demo chain.
    Jeśli widzi INVALID, to są rzeczywiste problemy z podpisem.
    """
    _set_leader_keys(monkeypatch, leader_id=1)
    
    storage = InMemoryStorage()
    storage.add_transaction(_make_transaction())
    proposal = build_block_proposal(storage)
    storage.add_block(proposal.block)
    
    # Usuń leader_id z bloku (symuluj stary format)
    block = storage.get_chain()[1]
    block_old = block.model_copy()
    block_old.leader_id = None
    storage._chain[1] = block_old
    
    # Weryfikuj
    result = verify_chain(storage)
    
    # Sprawdzenie: powinno być STALE, nie INVALID
    assert result["verification_status"] == "STALE", (
        f"Stale format chain should be STALE, not {result['verification_status']}"
    )
    assert result["valid"] is None, f"Stale chain should have valid=None, got {result['valid']}"
    
    # Sprawdź, że error ma is_stale flag
    errors = result.get("errors", [])
    if errors:
        first_error = errors[0]
        assert first_error.get("is_stale") is True, "Error should have is_stale=True"


def test_reset_demo_chain_clears_all_blocks_and_creates_valid_genesis(monkeypatch) -> None:
    """
    Test: reset demo chain powinien stworzyć pusty chain z genezą.
    """
    _set_leader_keys(monkeypatch, leader_id=1)
    
    storage = InMemoryStorage()
    storage.add_transaction(_make_transaction())
    proposal = build_block_proposal(storage)
    storage.add_block(proposal.block)
    
    assert len(storage.get_chain()) == 2  # genesis + 1 block
    
    # Reset
    genesis = storage.reset_demo_chain()
    
    # Sprawdzenia
    chain = storage.get_chain()
    assert len(chain) == 1, f"Expected 1 block (genesis), got {len(chain)}"
    assert chain[0].index == 0, "Genesis should have index 0"
    assert chain[0].hash == genesis.hash, "Genesis hash should match"
    
    # Weryfikuj
    result = verify_chain(storage)
    assert result["verification_status"] == "VALID"
    assert result["valid"] is True


def test_block_with_leader_id_but_no_signature_is_invalid_not_stale(monkeypatch) -> None:
    """
    Test: blok nowego formatu (ma leader_id) ale bez podpisu -> INVALID, nie STALE.
    
    Rozróżnienie:
    - Brak leader_id -> STALE (stary format, wymagany reset)
    - Ma leader_id ale brak podpisu -> INVALID (rzeczywisty problem)
    """
    _set_leader_keys(monkeypatch, leader_id=1)
    
    storage = InMemoryStorage()
    storage.add_transaction(_make_transaction())
    proposal = build_block_proposal(storage)
    block = proposal.block.model_copy()
    block.leader_sig = ""  # Usuń podpis
    
    result = verify_block_signature(block)
    
    assert result["ok"] is False
    assert result["reason"] == "missing leader_sig"
    assert result.get("is_stale") is False, "New format without signature is INVALID, not STALE"
    
    # Dodaj do chain i weryfikuj
    storage._chain.append(block)
    chain_result = verify_chain(storage)
    
    assert chain_result["verification_status"] == "INVALID"
    assert chain_result["valid"] is False


def test_gui_would_show_correct_colors_for_statuses(monkeypatch) -> None:
    """
    Test: GUI powinno pokazywać prawidłowe kolory na podstawie verification_status.
    """
    _set_leader_keys(monkeypatch, leader_id=1)
    
    from VetClinic.GUI.vetclinic_gui.windows.Admin.cluster_admin_widget import format_chain_verify_status
    
    # VALID -> zielony (ok)
    status, reason = format_chain_verify_status({
        "verification_status": "VALID",
        "valid": True,
        "errors": []
    })
    assert status == "VALID"
    assert reason == "ok"
    
    # STALE -> pomarańczowy (ale nie czerwony!)
    status, reason = format_chain_verify_status({
        "verification_status": "STALE",
        "valid": None,
        "errors": [{
            "height": 1,
            "reason": "stale chain format: missing leader_id"
        }]
    })
    assert status == "STALE"
    assert reason != "ok"
    assert "stale" in reason.lower()
    
    # INVALID -> czerwony (rzeczywisty problem)
    status, reason = format_chain_verify_status({
        "verification_status": "INVALID",
        "valid": False,
        "errors": [{
            "height": 1,
            "leader_id": 1,
            "reason": "invalid leader_sig for leader_id=1"
        }]
    })
    assert status == "INVALID"
    assert "invalid leader_sig" in reason
