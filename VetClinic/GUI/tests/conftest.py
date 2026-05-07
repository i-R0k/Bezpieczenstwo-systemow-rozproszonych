import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_OPENGL", "software")
os.environ.setdefault("QSG_RHI_BACKEND", "software")

import sys
from pathlib import Path

import pytest

# Ensure Qt runs offscreen before any PyQt import.
def pytest_configure():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


# Ensure the GUI package is importable when tests are run from repo root.
GUI_ROOT = Path(__file__).resolve().parents[1]
if str(GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(GUI_ROOT))

# Allow importing API package when GUI services still reference vetclinic_api.
API_ROOT = Path(__file__).resolve().parents[2] / "API"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

try:
    from bft_qt import QtWidgets
except Exception as exc:  # pragma: no cover - environment dependent
    pytest.skip(
        f"PyQt5 or PyQt6 is required for GUI tests; install requirements-gui.txt: {exc}",
        allow_module_level=True,
    )


@pytest.fixture(scope="session")
def qapp():
    """
    Override pytest-qt's qapp to keep a shared QApplication alive without
    hard-closing it at session end (mitigates teardown crashes on Windows).
    """
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(["pytest"])
    app.setQuitOnLastWindowClosed(False)
    yield app
    app.processEvents()

@pytest.fixture
def app(qapp):
    """
    Backward-compatible alias so tests expecting 'app' still receive the shared QApplication.
    """
    return qapp


@pytest.fixture(autouse=True)
def _close_all_qt_after_each_test(qtbot):
    """
    Ensure all tracked Qt widgets are closed between tests to avoid teardown crashes.
    """
    yield
    # Pump the event loop before and after closing tracked widgets.
    qtbot.wait(1)
    for widget in list(getattr(qtbot, "_active_widgets", [])):
        try:
            widget.close()
        except Exception:
            pass
    qtbot.wait(1)


@pytest.fixture(autouse=True)
def _cleanup_qt_widgets(qapp):
    """
    Final guard: close and delete any top-level widgets that may still be alive.
    """
    yield
    for w in list(QtWidgets.QApplication.topLevelWidgets()):
        try:
            w.close()
            w.deleteLater()
        except Exception:
            pass
    qapp.processEvents()
