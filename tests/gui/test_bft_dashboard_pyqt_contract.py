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
    from VetClinic.GUI.bft_api_client import BftApiClient
    from VetClinic.GUI.bft_dashboard import BftDashboardWindow
    from VetClinic.GUI.bft_qt import QtWidgets
    from VetClinic.GUI.bft_widgets import LogTable, MetricCard
    from VetClinic.GUI.vetclinic_gui.windows.Admin.bft_dashboard_widget import (
        AdminBftDashboardWidget,
    )
except Exception as exc:  # pragma: no cover - environment dependent
    pytest.skip(
        f"PyQt5/PyQt6 is required for GUI tests; install requirements-gui.txt: {exc}",
        allow_module_level=True,
    )


def test_bft_api_client_builds_urls_and_admin_header() -> None:
    client = BftApiClient("http://127.0.0.1:8000/", admin_token="secret-token")

    assert client._url("/bft/status") == "http://127.0.0.1:8000/bft/status"
    assert client._headers() == {"X-BFT-Admin-Token": "secret-token"}


def test_bft_dashboard_window_initializes_with_expected_tabs(qapp) -> None:
    window = BftDashboardWindow(
        base_url="http://127.0.0.1:8000",
        admin_token="hidden-token",
    )
    tabs = window.dashboard.tabs
    labels = [tabs.tabText(index) for index in range(tabs.count())]

    assert labels == [
        "Overview",
        "Protocols",
        "Live logs",
        "Demo actions",
        "Fault injection",
        "Security / 2FA / transport",
    ]
    label_texts = [label.text() for label in window.findChildren(QtWidgets.QLabel)]
    assert "hidden-token" not in label_texts
    window.close()


def test_bft_dashboard_is_available_for_admin_panel(qapp) -> None:
    widget = AdminBftDashboardWidget()
    assert widget.tabs.tabText(0) == "Overview"
    widget.close()


def test_log_table_accepts_empty_lists(qapp) -> None:
    table = LogTable()
    table.set_events([])
    assert table.rowCount() == 0
    table.set_communication([])
    assert table.rowCount() == 0


def test_metric_card_can_be_created(qapp) -> None:
    card = MetricCard("Operation count", 0, "demo")
    assert card.title_label.text() == "Operation count"
    assert card.value_label.text() == "0"
