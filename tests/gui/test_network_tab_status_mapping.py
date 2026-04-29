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
    from VetClinic.GUI.vetclinic_gui.windows.Admin.cluster_admin_widget import format_chain_verify_status
except Exception as exc:  # pragma: no cover - environment dependent
    pytest.skip(
        f"PyQt5/PyQt6 is required for GUI tests; install requirements-gui.txt: {exc}",
        allow_module_level=True,
    )


def test_valid_status_maps_to_valid_label() -> None:
    status, reason = format_chain_verify_status({"valid": True, "errors": []})
    assert status == "VALID"
    assert reason == "-"


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
            "valid": False,
            "errors": [{"height": 4, "reason": "stale chain format: missing leader_id"}],
        }
    )
    assert status == "INVALID"
    assert reason == "verify failed at height=4: stale chain format: missing leader_id"
