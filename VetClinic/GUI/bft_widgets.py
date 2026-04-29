from __future__ import annotations

import json
from typing import Any

from .bft_qt import ALIGN_CENTER, READONLY_EDIT_TRIGGER, STRETCH_MODE, QtWidgets


STATUS_COLORS = {
    "ALIVE": "#16a34a",
    "SUSPECT": "#ca8a04",
    "DEAD": "#dc2626",
    "RECOVERING": "#2563eb",
    "ERROR": "#dc2626",
    "UNKNOWN": "#6b7280",
}


class StatusBadge(QtWidgets.QLabel):
    def __init__(self, status: str = "UNKNOWN", parent=None) -> None:
        super().__init__(parent)
        self.setAlignment(ALIGN_CENTER)
        self.set_status(status)

    def set_status(self, status: str) -> None:
        normalized = (status or "UNKNOWN").upper()
        color = STATUS_COLORS.get(normalized, STATUS_COLORS["UNKNOWN"])
        self.setText(normalized)
        self.setStyleSheet(
            f"background:{color}; color:white; border-radius:8px; padding:4px 8px; font-weight:600;"
        )


class MetricCard(QtWidgets.QFrame):
    def __init__(self, title: str, value: str | int = "-", subtitle: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel if hasattr(QtWidgets.QFrame, "Shape") else QtWidgets.QFrame.StyledPanel)
        self.setStyleSheet("QFrame { border:1px solid #d1d5db; border-radius:6px; background:#ffffff; }")
        layout = QtWidgets.QVBoxLayout(self)
        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setStyleSheet("color:#475569; font-size:12px;")
        self.value_label = QtWidgets.QLabel(str(value))
        self.value_label.setStyleSheet("color:#111827; font-size:24px; font-weight:700;")
        self.subtitle_label = QtWidgets.QLabel(subtitle)
        self.subtitle_label.setStyleSheet("color:#64748b; font-size:11px;")
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.subtitle_label)

    def set_value(self, value: Any, subtitle: str | None = None) -> None:
        self.value_label.setText(str(value))
        if subtitle is not None:
            self.subtitle_label.setText(subtitle)


class JsonPreviewDialog(QtWidgets.QDialog):
    def __init__(self, title: str, payload: Any, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(760, 520)
        layout = QtWidgets.QVBoxLayout(self)
        self.text = QtWidgets.QTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlainText(json.dumps(payload, indent=2, ensure_ascii=False))
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(self.text)
        layout.addWidget(close_btn)


class LogTable(QtWidgets.QTableWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setEditTriggers(READONLY_EDIT_TRIGGER)
        self.horizontalHeader().setSectionResizeMode(STRETCH_MODE)

    def _fill(self, rows: list[dict[str, Any]], columns: list[str]) -> None:
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        self.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            for col_idx, key in enumerate(columns):
                value = row.get(key)
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                self.setItem(row_idx, col_idx, QtWidgets.QTableWidgetItem("" if value is None else str(value)))

    def set_events(self, events: list[dict[str, Any]]) -> None:
        self._fill(
            events or [],
            ["timestamp", "protocol", "status", "operation_id", "message"],
        )

    def set_communication(self, messages: list[dict[str, Any]]) -> None:
        self._fill(
            messages or [],
            ["timestamp", "protocol", "message_kind", "source_node_id", "target_node_id", "operation_id", "message"],
        )
