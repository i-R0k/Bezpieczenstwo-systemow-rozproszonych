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


def test_bft_api_client_can_set_swim_member_status(monkeypatch) -> None:
    calls = []

    def fake_request(self, method, path, **kwargs):
        calls.append((method, path, kwargs))
        return {"ok": True, "node_id": 2, "status": "ALIVE"}

    monkeypatch.setattr(BftApiClient, "_request", fake_request)
    client = BftApiClient("http://127.0.0.1:8000/")

    payload = client.set_swim_member_status(2, "ALIVE")

    assert payload["status"] == "ALIVE"
    assert calls == [("PUT", "/bft/swim/members/2/alive", {})]


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
    assert "S1: Cluster" in button_texts
    assert "S2: Full BFT" in button_texts
    assert "S3: BFT logic" in button_texts
    assert "S4: Recovery logic" in button_texts
    assert "Apply SWIM status" in button_texts
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


def test_bft_dashboard_scenario_3_logical_processes_passes(qapp, monkeypatch) -> None:
    scenario_name = "Scenario 3 - logical processes"
    widget = BftDashboardWidget(base_url="http://127.0.0.1:8001")
    widget.timer.stop()
    monkeypatch.setattr(widget, "_show_json", lambda *args, **kwargs: None)
    monkeypatch.setattr(widget, "refresh_all", lambda: None)
    report = {
        "ok": True,
        "status": "ok",
        "operation_id": "operation-1",
        "final_operation_status": "EXECUTED",
        "checkpoint_id": "checkpoint-1",
        "recovered_node_id": 3,
        "steps": [
            {"name": "Submit operation", "details": {"operation_id": "operation-1", "status": "RECEIVED"}},
            {"name": "Narwhal", "details": {"batch_id": "batch-1", "certificate": {"batch_id": "batch-1"}}},
            {"name": "HotStuff", "details": {"proposal_id": "proposal-1", "qc_id": "qc-1", "commit_id": "commit-1"}},
            {"name": "Execute", "details": {"status": "EXECUTED"}},
            {"name": "Checkpoint", "details": {"checkpoint_id": "checkpoint-1", "state_hash": "hash-1"}},
            {"name": "Recovery", "details": {"node_id": 3, "status": "RECOVERED"}},
        ],
    }
    events = {
        "ok": True,
        "events": [
            {"message": "batch_created"},
            {"message": "batch_certified"},
            {"message": "hotstuff_proposal_created"},
            {"message": "hotstuff_vote_recorded"},
            {"message": "hotstuff_qc_formed"},
            {"message": "hotstuff_block_committed"},
            {"message": "checkpoint_certificate_formed"},
            {"message": "state_transfer_applied"},
        ],
    }

    monkeypatch.setattr(BftApiClient, "clear_faults", lambda self: {"ok": True})
    monkeypatch.setattr(BftApiClient, "run_full_demo", lambda self: report)
    monkeypatch.setattr(BftApiClient, "get_events", lambda self, limit=50: events)
    monkeypatch.setattr(
        BftApiClient,
        "get_communication_log",
        lambda self, limit=50: {"ok": True, "messages": [{"message_kind": "PROPOSAL"}]},
    )

    widget.run_schedule_scenario_logical_processes()

    output = widget.demo_output.toPlainText()
    assert "'passed': True" in output
    assert scenario_name in output
    assert "HotStuff consensus" in output
    assert "Recovery/state transfer" in output
    widget.close()


def test_bft_dashboard_scenario_4_recovery_process_passes(qapp, monkeypatch) -> None:
    scenario_name = "Scenario 4 - recovery logical process"
    widget = BftDashboardWidget(base_url="http://127.0.0.1:8001")
    widget.timer.stop()
    calls = []
    monkeypatch.setattr(widget, "_show_json", lambda *args, **kwargs: None)
    monkeypatch.setattr(widget, "refresh_all", lambda: None)

    def fake_set_status(self, node_id, status):
        calls.append((node_id, status))
        return {
            "ok": True,
            "node_id": node_id,
            "status": status,
            "incarnation": len(calls),
            "suspicion_count": 0,
        }

    monkeypatch.setattr(BftApiClient, "clear_faults", lambda self: {"ok": True})
    monkeypatch.setattr(
        BftApiClient,
        "run_full_demo",
        lambda self: {"ok": True, "status": "ok", "checkpoint_id": "checkpoint-1", "recovered_node_id": 3},
    )
    monkeypatch.setattr(BftApiClient, "set_swim_member_status", fake_set_status)
    monkeypatch.setattr(
        BftApiClient,
        "get_swim_status",
        lambda self: {"ok": True, "alive": 6, "suspect": 0, "dead": 0, "recovering": 0},
    )
    monkeypatch.setattr(BftApiClient, "get_events", lambda self, limit=50: {"ok": True, "events": []})
    monkeypatch.setattr(BftApiClient, "get_communication_log", lambda self, limit=50: {"ok": True, "messages": []})

    widget.run_schedule_scenario_recovery_process()

    output = widget.demo_output.toPlainText()
    assert calls == [(2, "DEAD"), (2, "RECOVERING"), (2, "ALIVE")]
    assert "'passed': True" in output
    assert scenario_name in output
    assert "Failure detection" in output
    assert "Membership rejoin" in output
    widget.close()


def test_bft_dashboard_can_mark_dead_node_alive(qapp, monkeypatch) -> None:
    widget = BftDashboardWidget(base_url="http://127.0.0.1:8001")
    widget.timer.stop()
    calls = []
    monkeypatch.setattr(widget, "_show_json", lambda *args, **kwargs: None)
    monkeypatch.setattr(widget, "refresh_all", lambda: None)

    def fake_set_status(self, node_id, status):
        calls.append((node_id, status))
        return {"ok": True, "node_id": node_id, "status": status}

    monkeypatch.setattr(BftApiClient, "set_swim_member_status", fake_set_status)
    widget.swim_node_spin.setValue(2)
    widget.swim_status_combo.setCurrentText("ALIVE")

    widget.apply_swim_member_status()

    assert calls == [(2, "ALIVE")]
    assert "'status': 'ALIVE'" in widget.demo_output.toPlainText()
    widget.close()


def test_bft_dashboard_protocols_show_fault_indicators(qapp) -> None:
    widget = BftDashboardWidget(base_url="http://127.0.0.1:8001")
    widget.timer.stop()
    payloads = {
        "status": {
            "narwhal": {"batch_count": 0},
            "hotstuff": {"view": 0, "proposal_count": 0, "qc_count": 0, "commit_count": 0},
        },
        "hotstuff": {"view_state": {"leader_id": 1}},
        "narwhal": {"total_batches": 0, "tips": []},
        "swim": {"alive": 6, "suspect": 0, "dead": 0, "recovering": 0},
        "checkpointing": {"snapshots": [], "certificates": []},
        "recovery": {"transfers": [], "recovered_nodes": []},
        "faults": {
            "rules": [{"rule_id": "rule-1"}],
            "injected_faults": [{"fault_id": "fault-1"}],
            "partitions": [{"partition_id": "partition-1"}],
        },
    }

    widget._update_protocols(payloads)

    assert widget.protocol_cards["fault_rules"].value_label.text() == "1"
    assert widget.protocol_cards["fault_injected"].value_label.text() == "1"
    assert widget.protocol_cards["fault_partitions"].value_label.text() == "1"
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
