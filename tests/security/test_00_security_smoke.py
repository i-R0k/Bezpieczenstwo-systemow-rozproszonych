from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_security_bft_router_smoke(security_bft_client):
    assert security_bft_client.get("/bft/architecture").status_code == 200
    assert security_bft_client.get("/bft/status").status_code != 500


def test_security_full_app_exposes_bft_router(security_full_app_client):
    assert security_full_app_client.get("/bft/architecture").status_code == 200


def test_security_documentation_contract():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "testy bezpieczenstwa" in readme.lower() or "docs/SECURITY_TEST_PLAN.md" in readme
    assert (ROOT / "docs" / "THREAT_MODEL.md").exists()
    assert (ROOT / "docs" / "SECURITY_TEST_PLAN.md").exists()

