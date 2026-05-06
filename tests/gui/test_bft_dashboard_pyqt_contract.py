from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from VetClinic.GUI.bft_api_client import BftApiClient
    from VetClinic.GUI.bft_dashboard import BftDashboardWidget, BftDashboardWindow
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


def test_bft_dashboard_runner_help_returns_cli_options() -> None:
    completed = subprocess.run(
        [sys.executable, "VetClinic/GUI/run_bft_dashboard.py", "--help"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert completed.returncode == 0
    assert "--base-url" in completed.stdout
    assert "--admin-token" in completed.stdout


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
    button_texts = [button.text() for button in window.findChildren(QtWidgets.QPushButton)]
    assert "Scenario 1: Cluster dashboard" in button_texts
    assert "Scenario 2: Full BFT operation" in button_texts
    window.close()


def test_bft_dashboard_warns_when_status_reports_standalone_without_peers(qapp) -> None:
    widget = BftDashboardWidget()
    widget.timer.stop()

    status = {"ok": True, "quorum": {"summary": {"nodes": 1, "quorum": 1}}}
    assert widget._maybe_show_standalone_peers_warning(status) is True

    assert (
        "You are connected to standalone API without PEERS. Use Docker node1 http://127.0.0.1:8001"
        in widget.status_label.text()
    )
    widget.close()


def test_bft_dashboard_docker_node1_preset_updates_base_url(qapp) -> None:
    widget = BftDashboardWidget()
    widget.timer.stop()

    docker_index = widget.environment_preset_combo.findText("Docker node1")
    widget.environment_preset_combo.setCurrentIndex(docker_index)

    assert widget.base_url_input.text() == "http://127.0.0.1:8001"
    widget.close()


def test_bft_dashboard_auto_selects_docker_node1_when_probe_reports_six(monkeypatch) -> None:
    def fake_get_status(self):
        if self.base_url == "http://127.0.0.1:8001":
            return {
                "ok": True,
                "cluster_topology": {"configured_total_nodes": 6},
            }
        return {"ok": False, "error": "offline"}

    monkeypatch.delenv("BFT_DASHBOARD_BASE_URL", raising=False)
    monkeypatch.setattr(BftApiClient, "get_status", fake_get_status)

    assert BftDashboardWidget._resolve_initial_base_url(None) == "http://127.0.0.1:8001"


def test_bft_dashboard_standalone_warning_uses_topology_payload(qapp) -> None:
    widget = BftDashboardWidget(base_url="http://127.0.0.1:8000")
    widget.timer.stop()

    status = {
        "ok": True,
        "cluster_topology": {
            "configured_total_nodes": 1,
            "warning": "standalone/no peers: this API process has no PEERS configured",
        },
    }

    assert widget._maybe_show_standalone_peers_warning(status) is True
    assert "standalone/no peers" in widget.status_label.text()
    widget.close()


def test_bft_dashboard_does_not_hardcode_six_nodes(monkeypatch) -> None:
    monkeypatch.delenv("BFT_DASHBOARD_BASE_URL", raising=False)
    monkeypatch.setattr(
        BftApiClient,
        "get_status",
        lambda self: {"ok": True, "cluster_topology": {"configured_total_nodes": 5}},
    )

    assert BftDashboardWidget._resolve_initial_base_url(None) == "http://127.0.0.1:8000"


def test_bft_dashboard_scenario_1_cluster_dashboard_passes_with_docker_topology(
    qapp,
    monkeypatch,
) -> None:
    scenario_name = "Scenario 1 - poprawne uruchomienie klastra i dashboardu"
    widget = BftDashboardWidget(base_url="http://127.0.0.1:8001")
    widget.timer.stop()
    monkeypatch.setattr(widget, "_show_json", lambda *args, **kwargs: None)
    monkeypatch.setattr(widget, "refresh_all", lambda: None)
    monkeypatch.setattr(
        BftApiClient,
        "get_status",
        lambda self: {
            "ok": True,
            "cluster_topology": {"configured_total_nodes": 6},
            "quorum": {"summary": {"nodes": 6, "quorum": 4}},
        },
    )
    monkeypatch.setattr(
        BftApiClient,
        "get_cluster_topology",
        lambda self: {"ok": True, "configured_total_nodes": 6, "warning": None},
    )
    monkeypatch.setattr(
        BftApiClient,
        "get_chain_status",
        lambda self: {"ok": True, "height": 0},
    )
    monkeypatch.setattr(
        BftApiClient,
        "get_chain_verify",
        lambda self: {"ok": True, "verification_status": "VALID"},
    )

    widget.run_schedule_scenario_cluster_dashboard()

    assert "'passed': True" in widget.demo_output.toPlainText()
    assert scenario_name in widget.demo_output.toPlainText()
    widget.close()


def test_bft_dashboard_scenario_2_full_bft_operation_passes(qapp, monkeypatch) -> None:
    scenario_name = "Scenario 2 - pelny przebieg operacji klienta przez BFT"
    widget = BftDashboardWidget(base_url="http://127.0.0.1:8001")
    widget.timer.stop()
    monkeypatch.setattr(widget, "_show_json", lambda *args, **kwargs: None)
    monkeypatch.setattr(widget, "refresh_all", lambda: None)
    report = {
        "ok": True,
        "status": "ok",
        "final_operation_status": "EXECUTED",
        "checkpoint_id": "checkpoint-1",
        "recovered_node_id": 3,
        "steps": [
            {"name": "Submit operation"},
            {"name": "Narwhal"},
            {"name": "HotStuff"},
            {"name": "Execute"},
            {"name": "Checkpoint"},
            {"name": "Recovery"},
        ],
    }
    monkeypatch.setattr(BftApiClient, "clear_faults", lambda self: {"ok": True})
    monkeypatch.setattr(BftApiClient, "run_full_demo", lambda self: report)
    monkeypatch.setattr(BftApiClient, "get_last_report", lambda self: report)

    widget.run_schedule_scenario_full_bft_operation()

    assert "'passed': True" in widget.demo_output.toPlainText()
    assert scenario_name in widget.demo_output.toPlainText()
    widget.close()


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
