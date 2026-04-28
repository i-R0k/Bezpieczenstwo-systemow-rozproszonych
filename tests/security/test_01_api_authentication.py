from __future__ import annotations


ADMIN_TOKEN = "test-admin-token"


def _fault_rule_payload() -> dict:
    return {
        "fault_type": "DROP",
        "protocol": "HOTSTUFF",
        "message_kind": "VOTE",
        "probability": 1.0,
    }


def test_demo_mode_allows_bft_admin_demo_endpoint_without_token(monkeypatch, security_bft_client):
    monkeypatch.delenv("BFT_SECURITY_MODE", raising=False)
    monkeypatch.delenv("BFT_ADMIN_TOKEN", raising=False)

    response = security_bft_client.post("/bft/faults/rules", json=_fault_rule_payload())

    assert response.status_code == 200


def test_strict_mode_without_configured_admin_token_reports_misconfiguration(
    monkeypatch,
    security_bft_client,
):
    monkeypatch.setenv("BFT_SECURITY_MODE", "strict")
    monkeypatch.delenv("BFT_ADMIN_TOKEN", raising=False)

    response = security_bft_client.post("/bft/faults/rules", json=_fault_rule_payload())

    assert response.status_code in {500, 503}
    assert "BFT_ADMIN_TOKEN" in response.text


def test_strict_mode_requires_valid_admin_token(monkeypatch, security_bft_client):
    monkeypatch.setenv("BFT_SECURITY_MODE", "strict")
    monkeypatch.setenv("BFT_ADMIN_TOKEN", ADMIN_TOKEN)

    missing = security_bft_client.post("/bft/faults/rules", json=_fault_rule_payload())
    wrong = security_bft_client.post(
        "/bft/faults/rules",
        json=_fault_rule_payload(),
        headers={"X-BFT-Admin-Token": "wrong"},
    )
    correct = security_bft_client.post(
        "/bft/faults/rules",
        json=_fault_rule_payload(),
        headers={"X-BFT-Admin-Token": ADMIN_TOKEN},
    )

    assert missing.status_code in {401, 403}
    assert wrong.status_code in {401, 403}
    assert correct.status_code in {200, 201}


def test_public_bft_status_and_health_do_not_require_token_in_strict_mode(
    monkeypatch,
    security_bft_client,
):
    monkeypatch.setenv("BFT_SECURITY_MODE", "strict")
    monkeypatch.setenv("BFT_ADMIN_TOKEN", ADMIN_TOKEN)

    assert security_bft_client.get("/bft/status").status_code == 200
    assert security_bft_client.get("/bft/observability/health").status_code == 200

