from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from vetclinic_api.routers.security_demo import router as security_demo_router


ROOT = Path(__file__).resolve().parents[2]


def test_schedule_compliance_documents_cover_required_scope() -> None:
    schedule = ROOT / "docs" / "ZGODNOSC_Z_HARMONOGRAMEM.md"
    assert schedule.exists()
    text = schedule.read_text(encoding="utf-8")
    lowered = text.lower()

    for keyword in [
        "grpc",
        ".proto",
        "mtls",
        "2fa",
        "totp",
        "gui",
        "dashboard",
        "komunikacja miedzy procesami",
        "narwhal",
        "hotstuff",
        "swim",
        "checkpointing",
        "state transfer",
        "recovery",
        "fault injection",
        "pentest",
    ]:
        assert keyword in lowered

    for path in [
        "proto/bft.proto",
        "docs/GRPC.md",
        "docs/MTLS.md",
        "docs/2FA_TOTP.md",
        "docs/GUI_BFT.md",
    ]:
        assert (ROOT / path).exists()


def test_final_schedule_surface_endpoints_are_available(bft_client) -> None:
    for path in [
        "/bft/grpc/contract",
        "/bft/security/transport",
        "/bft/dashboard",
        "/bft/communication/log",
    ]:
        response = bft_client.get(path)
        assert response.status_code == 200


def test_security_2fa_demo_setup_endpoint_is_available() -> None:
    app = FastAPI()
    app.include_router(security_demo_router)
    client = TestClient(app)

    response = client.post(
        "/security/2fa/demo/setup",
        json={"account_name": "schedule@example.test"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["account_name"] == "schedule@example.test"
    assert payload["provisioning_uri"].startswith("otpauth://")


def test_readme_links_schedule_compliance_document() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/ZGODNOSC_Z_HARMONOGRAMEM.md" in readme
