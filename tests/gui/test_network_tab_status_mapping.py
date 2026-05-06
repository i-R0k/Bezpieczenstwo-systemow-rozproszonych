from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from VetClinic.GUI.vetclinic_gui.windows.Admin import cluster_admin_widget
    from VetClinic.GUI.vetclinic_gui.windows.Admin.cluster_admin_widget import (
        ClusterAdminWidget,
        format_chain_verify_status,
    )
except Exception as exc:  # pragma: no cover - environment dependent
    pytest.skip(
        f"PyQt5/PyQt6 is required for GUI tests; install requirements-gui.txt: {exc}",
        allow_module_level=True,
    )


def test_valid_status_maps_to_valid_label() -> None:
    status, reason = format_chain_verify_status({"verification_status": "VALID", "valid": True, "errors": []})
    assert status == "VALID"
    assert reason == "ok"


def test_invalid_status_uses_diagnostic_reason() -> None:
    status, reason = format_chain_verify_status(
        {
            "valid": False,
            "errors": [
                {
                    "height": 7,
                    "leader_id": 3,
                    "reason": "invalid leader_sig for leader_id=3",
                }
            ],
        }
    )
    assert status == "INVALID"
    assert reason == "verify failed at height=7: invalid leader_sig for leader_id=3"


def test_stale_format_is_not_rewritten_to_plain_invalid_signature() -> None:
    status, reason = format_chain_verify_status(
        {
            "verification_status": "STALE",
            "valid": None,
            "errors": [{"height": 4, "reason": "stale chain format: missing leader_id"}],
        }
    )
    assert status == "STALE"
    assert reason == "verify failed at height=4: stale chain format: missing leader_id"


def test_unverified_status_is_distinct_from_invalid() -> None:
    status, reason = format_chain_verify_status(
        {"verification_status": "UNVERIFIED", "reason": "node response unavailable"}
    )
    assert status == "UNVERIFIED"
    assert reason == "node response unavailable"


class _FakeResponse:
    def __init__(self, status_code: int = 200, payload: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text
        self.headers = {"content-type": "application/json"}

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_reset_demo_chain_all_nodes_uses_admin_token_header(monkeypatch, qapp) -> None:
    monkeypatch.setattr(ClusterAdminWidget, "refresh_cluster", lambda self: None)
    monkeypatch.setattr(ClusterAdminWidget, "_load_network_state", lambda self: None)
    widget = ClusterAdminWidget()
    widget.admin_token_input.setText("secret-token")
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return _FakeResponse(200, {"status": "ok"})

    monkeypatch.setattr(cluster_admin_widget.requests, "post", fake_post)

    widget.reset_demo_chain_all_nodes()

    assert calls
    assert all(call[1]["headers"] == {"X-BFT-Admin-Token": "secret-token"} for call in calls)
    widget.close()


def test_reset_demo_chain_without_token_keeps_demo_mode_headers_empty(monkeypatch, qapp) -> None:
    monkeypatch.setattr(ClusterAdminWidget, "refresh_cluster", lambda self: None)
    monkeypatch.setattr(ClusterAdminWidget, "_load_network_state", lambda self: None)
    widget = ClusterAdminWidget()
    calls = []

    def fake_post(url, **kwargs):
        calls.append(kwargs)
        return _FakeResponse(200, {"status": "ok"})

    monkeypatch.setattr(cluster_admin_widget.requests, "post", fake_post)

    widget.reset_demo_chain_all_nodes()

    assert calls
    assert all(call["headers"] == {} for call in calls)
    widget.close()


def test_reset_demo_chain_403_shows_admin_token_reason(monkeypatch, qapp) -> None:
    monkeypatch.setattr(ClusterAdminWidget, "refresh_cluster", lambda self: None)
    monkeypatch.setattr(ClusterAdminWidget, "_load_network_state", lambda self: None)
    widget = ClusterAdminWidget()

    monkeypatch.setattr(
        cluster_admin_widget.requests,
        "post",
        lambda *args, **kwargs: _FakeResponse(403, {"detail": "Forbidden"}),
    )

    widget.reset_demo_chain_all_nodes()

    assert "status_code" in widget.text_details.toPlainText()
    assert "admin token required; fill Admin token field" in widget.text_details.toPlainText()
    widget.close()
