from __future__ import annotations


def _assert_no_secret_markers(payload: str) -> None:
    lowered = payload.lower()
    for marker in [
        "private_key",
        "private_key_b64",
        "bft_admin_token",
        "leader_priv_key",
    ]:
        assert marker not in lowered


def test_grpc_runtime_status_exposes_no_secrets(security_bft_client) -> None:
    response = security_bft_client.get("/bft/grpc/runtime/status")

    assert response.status_code == 200
    _assert_no_secret_markers(response.text)
    assert "127.0.0.1" not in response.text


def test_grpc_runtime_ping_demo_uses_localhost_and_returns_no_secrets(security_bft_client) -> None:
    response = security_bft_client.post(
        "/bft/grpc/runtime/ping-demo",
        params={"source_node_id": 1, "target_node_id": 2},
    )

    assert response.status_code == 200
    _assert_no_secret_markers(response.text)
    assert response.json()["accepted"] is True


def test_grpc_runtime_ping_demo_requires_admin_token_in_strict_mode(
    security_bft_client,
    monkeypatch,
) -> None:
    monkeypatch.setenv("BFT_SECURITY_MODE", "strict")
    monkeypatch.setenv("BFT_ADMIN_TOKEN", "grpc-secret")

    response = security_bft_client.post("/bft/grpc/runtime/ping-demo")

    assert response.status_code in {401, 403}
