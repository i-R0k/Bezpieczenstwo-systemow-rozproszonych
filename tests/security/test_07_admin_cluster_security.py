from __future__ import annotations


ADMIN_TOKEN = "test-admin-token"


def test_admin_network_demo_mode_preserves_current_behavior(monkeypatch, security_full_app_client):
    monkeypatch.delenv("BFT_SECURITY_MODE", raising=False)
    monkeypatch.delenv("BFT_ADMIN_TOKEN", raising=False)

    response = security_full_app_client.put("/admin/network/state", json={"offline": False})

    assert response.status_code == 200


def test_admin_network_strict_mode_requires_admin_token(monkeypatch, security_full_app_client):
    monkeypatch.setenv("BFT_SECURITY_MODE", "strict")
    monkeypatch.setenv("BFT_ADMIN_TOKEN", ADMIN_TOKEN)

    missing = security_full_app_client.put("/admin/network/state", json={"offline": True})
    wrong = security_full_app_client.put(
        "/admin/network/state",
        json={"offline": True},
        headers={"X-BFT-Admin-Token": "wrong"},
    )
    correct = security_full_app_client.put(
        "/admin/network/state",
        json={"offline": False},
        headers={"X-BFT-Admin-Token": ADMIN_TOKEN},
    )

    assert missing.status_code in {401, 403}
    assert wrong.status_code in {401, 403}
    assert correct.status_code == 200


def test_cluster_peers_and_admin_state_do_not_expose_secrets(security_full_app_client):
    peers = security_full_app_client.get("/peers")
    state = security_full_app_client.get("/admin/network/state")
    combined = f"{peers.text}\n{state.text}".lower()

    assert peers.status_code == 200
    assert state.status_code == 200
    assert "private_key" not in combined
    assert "bft_admin_token" not in combined
    assert "leader_priv_key" not in combined


def test_invalid_network_state_values_are_controlled(security_full_app_client):
    response = security_full_app_client.put(
        "/admin/network/state",
        json={"slow_ms": -1, "drop_rpc_prob": 2.0, "flapping_mod": -10},
    )

    assert response.status_code != 500

