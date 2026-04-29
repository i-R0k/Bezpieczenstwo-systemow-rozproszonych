from __future__ import annotations

from datetime import datetime
from typing import Any

from .bft_api_client import BftApiClient
from .bft_qt import ALIGN_CENTER, PASSWORD_ECHO, STRETCH_MODE, QtCore, QtWidgets
from .bft_widgets import JsonPreviewDialog, LogTable, MetricCard, StatusBadge


def _section(payload: dict[str, Any], name: str) -> dict[str, Any]:
    value = payload.get(name)
    return value if isinstance(value, dict) else {}


def _count(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return "-"
        current = current.get(key)
    return "-" if current is None else current


class BftDashboardWidget(QtWidgets.QWidget):
    TAB_LABELS = [
        "Overview",
        "Protocols",
        "Live logs",
        "Demo actions",
        "Fault injection",
        "Security / 2FA / transport",
    ]

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        admin_token: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.client = BftApiClient(base_url=base_url, admin_token=admin_token)
        self.last_report: dict[str, Any] | None = None
        self._last_payloads: dict[str, dict[str, Any]] = {}
        self._build_ui(base_url, admin_token)
        self._connect_signals()
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.refresh_all)
        self.timer.start()

    def _build_ui(self, base_url: str, admin_token: str | None) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        self.toolbar = QtWidgets.QHBoxLayout()

        self.base_url_input = QtWidgets.QLineEdit(base_url)
        self.base_url_input.setObjectName("base_url_input")
        self.admin_token_input = QtWidgets.QLineEdit(admin_token or "")
        self.admin_token_input.setObjectName("admin_token_input")
        self.admin_token_input.setEchoMode(PASSWORD_ECHO)
        self.connect_button = QtWidgets.QPushButton("Connect/Test")
        self.auto_refresh = QtWidgets.QCheckBox("Auto-refresh")
        self.auto_refresh.setChecked(True)
        self.interval_combo = QtWidgets.QComboBox()
        for label, value in [("1s", 1000), ("2s", 2000), ("5s", 5000)]:
            self.interval_combo.addItem(label, value)
        self.interval_combo.setCurrentIndex(1)
        self.refresh_button = QtWidgets.QPushButton("Refresh now")

        self.toolbar.addWidget(QtWidgets.QLabel("Base URL"))
        self.toolbar.addWidget(self.base_url_input, 2)
        self.toolbar.addWidget(QtWidgets.QLabel("Admin token"))
        self.toolbar.addWidget(self.admin_token_input, 1)
        self.toolbar.addWidget(self.connect_button)
        self.toolbar.addWidget(self.auto_refresh)
        self.toolbar.addWidget(self.interval_combo)
        self.toolbar.addWidget(self.refresh_button)
        layout.addLayout(self.toolbar)

        self.tabs = QtWidgets.QTabWidget()
        self._build_overview_tab()
        self._build_protocols_tab()
        self._build_logs_tab()
        self._build_demo_tab()
        self._build_faults_tab()
        self._build_security_tab()
        layout.addWidget(self.tabs)

        self.status_label = QtWidgets.QLabel("API offline")
        self.status_label.setAlignment(ALIGN_CENTER)
        self.status_label.setStyleSheet("padding:6px; color:#334155;")
        layout.addWidget(self.status_label)

    def _build_overview_tab(self) -> None:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        grid = QtWidgets.QGridLayout()
        self.metric_cards: dict[str, MetricCard] = {}
        metrics = [
            ("total_nodes", "Total nodes"),
            ("quorum", "Quorum"),
            ("leader", "Current leader"),
            ("view", "Current view"),
            ("operations", "Operation count"),
            ("batches", "Batch count"),
            ("proposals", "Proposal count"),
            ("qcs", "QC count"),
            ("commits", "Commit count"),
            ("checkpoints", "Checkpoint count"),
            ("faults", "Active faults"),
        ]
        for idx, (key, title) in enumerate(metrics):
            card = MetricCard(title)
            self.metric_cards[key] = card
            grid.addWidget(card, idx // 4, idx % 4)
        layout.addLayout(grid)

        nodes_group = QtWidgets.QGroupBox("Cluster nodes")
        nodes_layout = QtWidgets.QGridLayout(nodes_group)
        self.node_badges: dict[int, StatusBadge] = {}
        for node_id in range(1, 7):
            box = QtWidgets.QVBoxLayout()
            label = QtWidgets.QLabel(f"node{node_id}")
            label.setAlignment(ALIGN_CENTER)
            badge = StatusBadge("UNKNOWN")
            self.node_badges[node_id] = badge
            box.addWidget(label)
            box.addWidget(badge)
            wrapper = QtWidgets.QWidget()
            wrapper.setLayout(box)
            nodes_layout.addWidget(wrapper, 0, node_id - 1)
        layout.addWidget(nodes_group)
        self.tabs.addTab(tab, "Overview")

    def _build_protocols_tab(self) -> None:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(tab)
        self.protocol_cards: dict[str, MetricCard] = {}
        items = [
            ("narwhal_batches", "Narwhal batches"),
            ("narwhal_dag", "DAG batches"),
            ("narwhal_tips", "DAG tips"),
            ("hotstuff_view", "HotStuff view"),
            ("hotstuff_leader", "HotStuff leader"),
            ("hotstuff_proposals", "Proposals"),
            ("hotstuff_qcs", "QCs"),
            ("hotstuff_commits", "Commits"),
            ("swim_alive", "SWIM alive"),
            ("swim_suspect", "SWIM suspect"),
            ("swim_dead", "SWIM dead"),
            ("swim_recovering", "SWIM recovering"),
            ("checkpoint_snapshots", "Snapshots"),
            ("checkpoint_certificates", "Certificates"),
            ("recovery_transfers", "Transfers"),
            ("recovery_nodes", "Recovered nodes"),
        ]
        for idx, (key, title) in enumerate(items):
            card = MetricCard(title)
            self.protocol_cards[key] = card
            layout.addWidget(card, idx // 4, idx % 4)
        self.tabs.addTab(tab, "Protocols")

    def _build_logs_tab(self) -> None:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        filter_row = QtWidgets.QHBoxLayout()
        self.protocol_filter = QtWidgets.QComboBox()
        for protocol in ["ALL", "NARWHAL", "HOTSTUFF", "SWIM", "FAULT_INJECTION", "CHECKPOINTING", "RECOVERY", "CRYPTO"]:
            self.protocol_filter.addItem(protocol)
        filter_row.addWidget(QtWidgets.QLabel("Protocol filter"))
        filter_row.addWidget(self.protocol_filter)
        filter_row.addStretch(1)
        layout.addLayout(filter_row)
        self.communication_table = LogTable()
        self.events_table = LogTable()
        layout.addWidget(QtWidgets.QLabel("Communication log"))
        layout.addWidget(self.communication_table)
        layout.addWidget(QtWidgets.QLabel("Recent events"))
        layout.addWidget(self.events_table)
        self.tabs.addTab(tab, "Live logs")

    def _build_demo_tab(self) -> None:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        row = QtWidgets.QHBoxLayout()
        self.run_demo_button = QtWidgets.QPushButton("Run full BFT demo")
        self.grpc_ping_button = QtWidgets.QPushButton("Run gRPC ping demo")
        self.refresh_all_button = QtWidgets.QPushButton("Refresh all")
        self.open_last_report_button = QtWidgets.QPushButton("Open last report JSON")
        self.clear_faults_button = QtWidgets.QPushButton("Clear faults")
        for button in [
            self.run_demo_button,
            self.grpc_ping_button,
            self.refresh_all_button,
            self.open_last_report_button,
            self.clear_faults_button,
        ]:
            row.addWidget(button)
        layout.addLayout(row)
        self.demo_output = QtWidgets.QTextEdit()
        self.demo_output.setReadOnly(True)
        layout.addWidget(self.demo_output)
        self.tabs.addTab(tab, "Demo actions")

    def _build_faults_tab(self) -> None:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        form = QtWidgets.QGridLayout()
        self.fault_type_combo = QtWidgets.QComboBox()
        for value in ["DROP", "DELAY", "DUPLICATE", "REPLAY", "EQUIVOCATION", "NETWORK_PARTITION", "LEADER_FAILURE"]:
            self.fault_type_combo.addItem(value)
        self.fault_protocol_combo = QtWidgets.QComboBox()
        for value in ["", "NARWHAL", "HOTSTUFF", "SWIM", "RECOVERY"]:
            self.fault_protocol_combo.addItem(value)
        self.message_kind_combo = QtWidgets.QComboBox()
        for value in ["", "BATCH", "BATCH_ACK", "PROPOSAL", "VOTE", "COMMIT", "SWIM_PING", "SWIM_GOSSIP", "STATE_TRANSFER"]:
            self.message_kind_combo.addItem(value)
        self.source_spin = QtWidgets.QSpinBox()
        self.source_spin.setRange(0, 999)
        self.target_spin = QtWidgets.QSpinBox()
        self.target_spin.setRange(0, 999)
        self.probability_spin = QtWidgets.QDoubleSpinBox()
        self.probability_spin.setRange(0.0, 1.0)
        self.probability_spin.setSingleStep(0.1)
        self.probability_spin.setValue(1.0)
        self.delay_spin = QtWidgets.QSpinBox()
        self.delay_spin.setRange(0, 60000)
        self.add_fault_button = QtWidgets.QPushButton("Add fault rule")
        self.clear_all_faults_button = QtWidgets.QPushButton("Clear all faults")
        fields = [
            ("fault_type", self.fault_type_combo),
            ("protocol", self.fault_protocol_combo),
            ("message_kind", self.message_kind_combo),
            ("source_node_id", self.source_spin),
            ("target_node_id", self.target_spin),
            ("probability", self.probability_spin),
            ("delay_ms", self.delay_spin),
        ]
        for idx, (label, widget) in enumerate(fields):
            form.addWidget(QtWidgets.QLabel(label), idx // 4 * 2, idx % 4)
            form.addWidget(widget, idx // 4 * 2 + 1, idx % 4)
        form.addWidget(self.add_fault_button, 4, 0)
        form.addWidget(self.clear_all_faults_button, 4, 1)
        layout.addLayout(form)
        self.fault_rules_table = QtWidgets.QTableWidget()
        self.fault_rules_table.setColumnCount(5)
        self.fault_rules_table.setHorizontalHeaderLabels(["rule_id", "fault_type", "protocol", "message_kind", "probability"])
        self.fault_rules_table.horizontalHeader().setSectionResizeMode(STRETCH_MODE)
        layout.addWidget(self.fault_rules_table)
        self.tabs.addTab(tab, "Fault injection")

    def _build_security_tab(self) -> None:
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        self.transport_text = QtWidgets.QTextEdit()
        self.transport_text.setReadOnly(True)
        self.grpc_text = QtWidgets.QTextEdit()
        self.grpc_text.setReadOnly(True)
        layout.addWidget(QtWidgets.QLabel("Transport status"))
        layout.addWidget(self.transport_text)
        layout.addWidget(QtWidgets.QLabel("gRPC runtime status"))
        layout.addWidget(self.grpc_text)

        form = QtWidgets.QGridLayout()
        self.totp_account_input = QtWidgets.QLineEdit("demo@example.test")
        self.totp_secret_output = QtWidgets.QLineEdit()
        self.totp_secret_output.setReadOnly(True)
        self.totp_uri_output = QtWidgets.QLineEdit()
        self.totp_uri_output.setReadOnly(True)
        self.totp_code_input = QtWidgets.QLineEdit()
        self.totp_setup_button = QtWidgets.QPushButton("Setup TOTP")
        self.totp_verify_button = QtWidgets.QPushButton("Verify code")
        self.totp_result_label = QtWidgets.QLabel("Not verified")
        form.addWidget(QtWidgets.QLabel("account_name"), 0, 0)
        form.addWidget(self.totp_account_input, 0, 1)
        form.addWidget(self.totp_setup_button, 0, 2)
        form.addWidget(QtWidgets.QLabel("secret"), 1, 0)
        form.addWidget(self.totp_secret_output, 1, 1, 1, 2)
        form.addWidget(QtWidgets.QLabel("provisioning_uri"), 2, 0)
        form.addWidget(self.totp_uri_output, 2, 1, 1, 2)
        form.addWidget(QtWidgets.QLabel("code"), 3, 0)
        form.addWidget(self.totp_code_input, 3, 1)
        form.addWidget(self.totp_verify_button, 3, 2)
        form.addWidget(self.totp_result_label, 4, 0, 1, 3)
        layout.addLayout(form)
        self.tabs.addTab(tab, "Security / 2FA / transport")

    def _connect_signals(self) -> None:
        self.connect_button.clicked.connect(self.connect_test)
        self.refresh_button.clicked.connect(self.refresh_all)
        self.refresh_all_button.clicked.connect(self.refresh_all)
        self.auto_refresh.toggled.connect(self._toggle_auto_refresh)
        self.interval_combo.currentIndexChanged.connect(self._change_interval)
        self.protocol_filter.currentIndexChanged.connect(self._apply_log_filter)
        self.run_demo_button.clicked.connect(self.run_full_demo)
        self.grpc_ping_button.clicked.connect(self.run_grpc_ping_demo)
        self.open_last_report_button.clicked.connect(self.open_last_report)
        self.clear_faults_button.clicked.connect(self.clear_faults)
        self.add_fault_button.clicked.connect(self.add_fault_rule)
        self.clear_all_faults_button.clicked.connect(self.clear_faults)
        self.totp_setup_button.clicked.connect(self.setup_totp)
        self.totp_verify_button.clicked.connect(self.verify_totp)

    def _sync_client(self) -> None:
        self.client = BftApiClient(
            base_url=self.base_url_input.text().strip() or "http://127.0.0.1:8000",
            admin_token=self.admin_token_input.text() or None,
        )

    def _set_status(self, message: str) -> None:
        self.status_label.setText(f"{self.client.base_url} | {message}")

    def _toggle_auto_refresh(self, enabled: bool) -> None:
        if enabled:
            self.timer.start()
        else:
            self.timer.stop()

    def _change_interval(self) -> None:
        self.timer.setInterval(int(self.interval_combo.currentData()))

    def connect_test(self) -> None:
        self._sync_client()
        payload = self.client.get_status()
        self._set_status("connected" if payload.get("ok") else f"API offline: {payload.get('error')}")
        self.refresh_all()

    def refresh_all(self) -> None:
        self._sync_client()
        payloads = {
            "status": self.client.get_status(),
            "events": self.client.get_events(),
            "communication": self.client.get_communication_log(),
            "swim": self.client.get_swim_status(),
            "hotstuff": self.client.get_hotstuff_status(),
            "narwhal": self.client.get_narwhal_dag(),
            "faults": self.client.get_faults_status(),
            "checkpointing": self.client.get_checkpointing_status(),
            "recovery": self.client.get_recovery_status(),
            "grpc": self.client.get_grpc_runtime_status(),
            "transport": self.client.get_security_transport(),
        }
        self._last_payloads = payloads
        if not payloads["status"].get("ok"):
            self._set_status(f"API offline: {payloads['status'].get('error')}")
        else:
            self._set_status(f"last refresh {datetime.now().strftime('%H:%M:%S')}")
        self._update_overview(payloads)
        self._update_protocols(payloads)
        self._update_logs(payloads)
        self._update_faults(payloads["faults"])
        self._update_security(payloads)

    def _update_overview(self, payloads: dict[str, dict[str, Any]]) -> None:
        status = payloads["status"]
        quorum = _section(status, "quorum")
        hotstuff = _section(status, "hotstuff")
        narwhal = _section(status, "narwhal")
        operations = _section(status, "operations")
        faults = _section(status, "fault_injection")
        checkpointing = _section(status, "checkpointing")
        swim = payloads["swim"]
        self.metric_cards["total_nodes"].set_value(_count(quorum, "summary", "nodes"))
        self.metric_cards["quorum"].set_value(_count(quorum, "summary", "quorum"))
        self.metric_cards["leader"].set_value(_count(payloads["hotstuff"], "view_state", "leader_id"))
        self.metric_cards["view"].set_value(_count(hotstuff, "view"))
        self.metric_cards["operations"].set_value(_count(operations, "count"))
        self.metric_cards["batches"].set_value(_count(narwhal, "batch_count"))
        self.metric_cards["proposals"].set_value(_count(hotstuff, "proposal_count"))
        self.metric_cards["qcs"].set_value(_count(hotstuff, "qc_count"))
        self.metric_cards["commits"].set_value(_count(hotstuff, "commit_count"))
        self.metric_cards["checkpoints"].set_value(_count(checkpointing, "certificates_count"))
        self.metric_cards["faults"].set_value(_count(faults, "rules_count"))
        members = swim.get("members", []) if isinstance(swim, dict) else []
        status_by_node = {member.get("node_id"): member.get("status") for member in members if isinstance(member, dict)}
        for node_id, badge in self.node_badges.items():
            badge.set_status(status_by_node.get(node_id, "UNKNOWN"))

    def _update_protocols(self, payloads: dict[str, dict[str, Any]]) -> None:
        status = payloads["status"]
        narwhal_status = _section(status, "narwhal")
        hotstuff_status = _section(status, "hotstuff")
        swim = payloads["swim"]
        checkpointing = payloads["checkpointing"]
        recovery = payloads["recovery"]
        self.protocol_cards["narwhal_batches"].set_value(_count(narwhal_status, "batch_count"))
        self.protocol_cards["narwhal_dag"].set_value(payloads["narwhal"].get("total_batches", "-"))
        self.protocol_cards["narwhal_tips"].set_value(len(payloads["narwhal"].get("tips", []) or []))
        self.protocol_cards["hotstuff_view"].set_value(_count(hotstuff_status, "view"))
        self.protocol_cards["hotstuff_leader"].set_value(_count(payloads["hotstuff"], "view_state", "leader_id"))
        self.protocol_cards["hotstuff_proposals"].set_value(_count(hotstuff_status, "proposal_count"))
        self.protocol_cards["hotstuff_qcs"].set_value(_count(hotstuff_status, "qc_count"))
        self.protocol_cards["hotstuff_commits"].set_value(_count(hotstuff_status, "commit_count"))
        for key in ["alive", "suspect", "dead", "recovering"]:
            self.protocol_cards[f"swim_{key}"].set_value(swim.get(key, "-"))
        self.protocol_cards["checkpoint_snapshots"].set_value(len(checkpointing.get("snapshots", []) or []))
        self.protocol_cards["checkpoint_certificates"].set_value(len(checkpointing.get("certificates", []) or []))
        self.protocol_cards["recovery_transfers"].set_value(len(recovery.get("transfers", []) or []))
        self.protocol_cards["recovery_nodes"].set_value(len(recovery.get("recovered_nodes", []) or []))

    def _filtered(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        selected = self.protocol_filter.currentText()
        if selected == "ALL":
            return rows
        return [row for row in rows if row.get("protocol") == selected]

    def _update_logs(self, payloads: dict[str, dict[str, Any]]) -> None:
        events = payloads["events"].get("events", []) or []
        messages = payloads["communication"].get("messages", []) or []
        self.events_table.set_events(self._filtered(events))
        self.communication_table.set_communication(self._filtered(messages))

    def _apply_log_filter(self) -> None:
        if self._last_payloads:
            self._update_logs(self._last_payloads)

    def _update_faults(self, faults: dict[str, Any]) -> None:
        rules = faults.get("rules", []) or []
        self.fault_rules_table.setRowCount(len(rules))
        for row_idx, rule in enumerate(rules):
            for col_idx, key in enumerate(["rule_id", "fault_type", "protocol", "message_kind", "probability"]):
                self.fault_rules_table.setItem(row_idx, col_idx, QtWidgets.QTableWidgetItem(str(rule.get(key, ""))))

    def _update_security(self, payloads: dict[str, dict[str, Any]]) -> None:
        self.transport_text.setPlainText(str(payloads["transport"]))
        self.grpc_text.setPlainText(str(payloads["grpc"]))

    def _show_json(self, title: str, payload: Any) -> None:
        dialog = JsonPreviewDialog(title, payload, self)
        dialog.exec()

    def run_full_demo(self) -> None:
        payload = self.client.run_full_demo()
        self.last_report = payload
        self.demo_output.setPlainText(str(payload))
        self._show_json("Full BFT demo", payload)
        self.refresh_all()

    def run_grpc_ping_demo(self) -> None:
        payload = self.client.run_grpc_ping_demo()
        self.demo_output.setPlainText(str(payload))
        self._show_json("gRPC ping demo", payload)
        self.refresh_all()

    def open_last_report(self) -> None:
        payload = self.client.get_last_report()
        self.last_report = payload
        self._show_json("Last BFT report", payload)

    def clear_faults(self) -> None:
        payload = self.client.clear_faults()
        self._show_json("Clear faults", payload)
        self.refresh_all()

    def add_fault_rule(self) -> None:
        payload: dict[str, Any] = {
            "fault_type": self.fault_type_combo.currentText(),
            "probability": self.probability_spin.value(),
        }
        for key, combo in [("protocol", self.fault_protocol_combo), ("message_kind", self.message_kind_combo)]:
            if combo.currentText():
                payload[key] = combo.currentText()
        if self.source_spin.value() > 0:
            payload["source_node_id"] = self.source_spin.value()
        if self.target_spin.value() > 0:
            payload["target_node_id"] = self.target_spin.value()
        if self.delay_spin.value() > 0:
            payload["delay_ms"] = self.delay_spin.value()
        result = self.client.create_fault_rule(payload)
        self._show_json("Add fault rule", result)
        self.refresh_all()

    def setup_totp(self) -> None:
        payload = self.client.setup_totp(self.totp_account_input.text().strip())
        if payload.get("ok"):
            self.totp_secret_output.setText(payload.get("secret", ""))
            self.totp_uri_output.setText(payload.get("provisioning_uri", ""))
        self._show_json("TOTP setup", payload)

    def verify_totp(self) -> None:
        payload = self.client.verify_totp(
            self.totp_account_input.text().strip() or None,
            self.totp_secret_output.text().strip() or None,
            self.totp_code_input.text().strip(),
        )
        self.totp_result_label.setText(f"valid={payload.get('valid')}")
        self._show_json("TOTP verify", payload)


class BftDashboardWindow(QtWidgets.QMainWindow):
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        admin_token: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("BSR BFT Protocol Dashboard")
        self.resize(1280, 820)
        self.dashboard = BftDashboardWidget(base_url=base_url, admin_token=admin_token, parent=self)
        self.setCentralWidget(self.dashboard)
        self.statusBar().showMessage(f"{base_url} | ready")
