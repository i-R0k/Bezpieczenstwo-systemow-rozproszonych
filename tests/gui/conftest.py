from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from VetClinic.GUI.bft_qt import QtWidgets
except Exception as exc:  # pragma: no cover - environment dependent
    pytest.skip(
        f"PyQt5/PyQt6 is required for GUI tests; install requirements-gui.txt: {exc}",
        allow_module_level=True,
    )


@pytest.fixture(scope="session")
def qapp():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    yield app
