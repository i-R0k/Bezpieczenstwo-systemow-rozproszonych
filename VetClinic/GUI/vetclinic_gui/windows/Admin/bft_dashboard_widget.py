from __future__ import annotations

import os
import sys
from pathlib import Path

GUI_ROOT = Path(__file__).resolve().parents[3]
PROJECT_GUI_PARENT = GUI_ROOT.parent
for path in (PROJECT_GUI_PARENT,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from GUI.bft_dashboard import BftDashboardWidget  # type: ignore  # noqa: E402


class AdminBftDashboardWidget(BftDashboardWidget):
    """BFT protocol dashboard embedded into the existing administrator panel."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            base_url=os.getenv("BFT_DASHBOARD_BASE_URL", "http://127.0.0.1:8000"),
            admin_token=os.getenv("BFT_ADMIN_TOKEN") or None,
            parent=parent,
        )
