from __future__ import annotations


ADMIN_TOKEN = "test-admin-token"


def test_strict_mode_blocks_destructive_bft_endpoints_without_token(
    monkeypatch,
    security_bft_client,
):
    monkeypatch.setenv("BFT_SECURITY_MODE", "strict")
    monkeypatch.setenv("BFT_ADMIN_TOKEN", ADMIN_TOKEN)

    checks = [
        security_bft_client.delete("/bft/operations"),
        security_bft_client.delete("/bft/faults"),
        security_bft_client.delete("/bft/crypto"),
        security_bft_client.post("/bft/crypto/demo-keys?total_nodes=6"),
        security_bft_client.post("/bft/recovery/nodes/3/recover-demo"),
    ]

    assert all(response.status_code in {401, 403} for response in checks)


def test_strict_mode_allows_admin_endpoint_with_valid_token(monkeypatch, security_bft_client):
    monkeypatch.setenv("BFT_SECURITY_MODE", "strict")
    monkeypatch.setenv("BFT_ADMIN_TOKEN", ADMIN_TOKEN)

    response = security_bft_client.post(
        "/bft/crypto/demo-keys?total_nodes=6",
        headers={"X-BFT-Admin-Token": ADMIN_TOKEN},
    )

    assert response.status_code == 200

