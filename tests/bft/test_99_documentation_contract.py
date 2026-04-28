from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_readme_contains_final_bft_keywords():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for keyword in [
        "Narwhal",
        "HotStuff",
        "SWIM",
        "fault injection",
        "checkpoint",
        "recovery",
        "crypto",
        "observability",
        "testbed",
    ]:
        assert keyword in readme


def test_final_documentation_files_exist():
    required_docs = [
        "ARCHITEKTURA.md",
        "NARWHAL.md",
        "HOTSTUFF.md",
        "SWIM.md",
        "FAULT_INJECTION.md",
        "CHECKPOINTING_RECOVERY.md",
        "CRYPTO_SECURITY.md",
        "OBSERVABILITY.md",
        "DEMO.md",
        "TESTBED.md",
        "ZGODNOSC_Z_HARMONOGRAMEM.md",
        "RAPORT_TECHNICZNY.md",
        "INSTRUKCJA_UZYTKOWNIKA.md",
        "SCENARIUSZ_PREZENTACJI.md",
        "API_BFT.md",
        "OGRANICZENIA.md",
    ]
    for filename in required_docs:
        assert (ROOT / "docs" / filename).exists()


def test_schedule_document_contains_main_areas():
    content = (ROOT / "docs" / "ZGODNOSC_Z_HARMONOGRAMEM.md").read_text(encoding="utf-8")
    for keyword in [
        "Narwhal",
        "HotStuff",
        "SWIM",
        "fault injection",
        "checkpointing",
        "state transfer",
        "replay",
        "monitoring",
        "testbed",
    ]:
        assert keyword in content


def test_presentation_scenario_contains_final_demo_commands():
    content = (ROOT / "docs" / "SCENARIUSZ_PREZENTACJI.md").read_text(encoding="utf-8")
    assert "python scripts/run_bft_testbed.py" in content
    assert "/bft/demo/run" in content

