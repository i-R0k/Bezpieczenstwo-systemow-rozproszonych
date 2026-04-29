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
