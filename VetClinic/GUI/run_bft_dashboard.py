from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from GUI.bft_dashboard import BftDashboardWindow  # type: ignore  # noqa: E402
from GUI.bft_qt import QtWidgets, exec_app  # type: ignore  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the BSR BFT PyQt dashboard")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--admin-token", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = QtWidgets.QApplication(sys.argv)
    window = BftDashboardWindow(base_url=args.base_url, admin_token=args.admin_token)
    window.show()
    return exec_app(app)


if __name__ == "__main__":
    raise SystemExit(main())
