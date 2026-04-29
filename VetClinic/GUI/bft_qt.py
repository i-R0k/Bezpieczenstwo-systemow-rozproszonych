from __future__ import annotations

try:  # Prefer the existing project GUI stack.
    from PyQt6 import QtCore, QtGui, QtWidgets

    QT_VERSION = "PyQt6"
    Qt = QtCore.Qt
    ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
    ALIGN_LEFT = Qt.AlignmentFlag.AlignLeft
    PASSWORD_ECHO = QtWidgets.QLineEdit.EchoMode.Password
    READONLY_EDIT_TRIGGER = QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
    STRETCH_MODE = QtWidgets.QHeaderView.ResizeMode.Stretch
except Exception:  # pragma: no cover - fallback for requirements-gui.txt users
    from PyQt5 import QtCore, QtGui, QtWidgets  # type: ignore

    QT_VERSION = "PyQt5"
    Qt = QtCore.Qt
    ALIGN_CENTER = Qt.AlignCenter
    ALIGN_LEFT = Qt.AlignLeft
    PASSWORD_ECHO = QtWidgets.QLineEdit.Password
    READONLY_EDIT_TRIGGER = QtWidgets.QAbstractItemView.NoEditTriggers
    STRETCH_MODE = QtWidgets.QHeaderView.Stretch


def exec_app(app: QtWidgets.QApplication) -> int:
    if hasattr(app, "exec"):
        return app.exec()
    return app.exec_()


def apply_light_theme(app: QtWidgets.QApplication) -> None:
    """Force a light Qt palette so the dashboard does not inherit OS dark mode."""
    app.setStyle("Fusion")
    palette = QtGui.QPalette()
    roles = getattr(QtGui.QPalette, "ColorRole", QtGui.QPalette)
    palette.setColor(roles.Window, QtGui.QColor("#f8fafc"))
    palette.setColor(roles.WindowText, QtGui.QColor("#111827"))
    palette.setColor(roles.Base, QtGui.QColor("#ffffff"))
    palette.setColor(roles.AlternateBase, QtGui.QColor("#f1f5f9"))
    palette.setColor(roles.ToolTipBase, QtGui.QColor("#ffffff"))
    palette.setColor(roles.ToolTipText, QtGui.QColor("#111827"))
    palette.setColor(roles.Text, QtGui.QColor("#111827"))
    palette.setColor(roles.Button, QtGui.QColor("#ffffff"))
    palette.setColor(roles.ButtonText, QtGui.QColor("#111827"))
    palette.setColor(roles.BrightText, QtGui.QColor("#ffffff"))
    palette.setColor(roles.Highlight, QtGui.QColor("#2563eb"))
    palette.setColor(roles.HighlightedText, QtGui.QColor("#ffffff"))
    app.setPalette(palette)
    app.setStyleSheet(
        """
        QWidget { background-color: #f8fafc; color: #111827; }
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            background-color: #ffffff;
            color: #111827;
            border: 1px solid #cbd5e1;
            border-radius: 4px;
            padding: 4px;
        }
        QTableWidget {
            background-color: #ffffff;
            color: #111827;
            gridline-color: #e5e7eb;
            alternate-background-color: #f8fafc;
        }
        QHeaderView::section {
            background-color: #e5e7eb;
            color: #111827;
            border: 1px solid #cbd5e1;
            padding: 4px;
        }
        QTabWidget::pane { border: 1px solid #cbd5e1; background: #ffffff; }
        QTabBar::tab {
            background: #e5e7eb;
            color: #111827;
            padding: 7px 12px;
            border: 1px solid #cbd5e1;
        }
        QTabBar::tab:selected { background: #ffffff; color: #111827; }
        QGroupBox {
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            margin-top: 12px;
            background-color: #ffffff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px;
            color: #334155;
        }
        QPushButton {
            background-color: #ffffff;
            color: #111827;
            border: 1px solid #cbd5e1;
            border-radius: 4px;
            padding: 6px 10px;
        }
        QPushButton:hover { background-color: #f1f5f9; }
        QPushButton:pressed { background-color: #e2e8f0; }
        QCheckBox, QLabel { color: #111827; }
        """
    )
