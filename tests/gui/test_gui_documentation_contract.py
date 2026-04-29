from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_gui_documentation_mentions_pyqt_dashboard() -> None:
    assert (ROOT / "VetClinic" / "GUI" / "README.md").exists()
    assert "PyQt" in (ROOT / "docs" / "GUI_BFT.md").read_text(encoding="utf-8")
    assert "PyQt BFT Dashboard" in (
        ROOT / "docs" / "SCENARIUSZ_PREZENTACJI.md"
    ).read_text(encoding="utf-8")
    assert "PyQt BFT Dashboard" in (ROOT / "README.md").read_text(encoding="utf-8")
    assert "VetClinic/GUI/bft_dashboard.py" in (
        ROOT / "docs" / "ZGODNOSC_Z_HARMONOGRAMEM.md"
    ).read_text(encoding="utf-8")
