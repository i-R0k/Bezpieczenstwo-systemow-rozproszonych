from __future__ import annotations


def test_crypto_router_contract(bft_client):
    keys = bft_client.post("/bft/crypto/demo-keys?total_nodes=3")
    assert keys.status_code == 200
    assert len(keys.json()["public_keys"]) == 3
    assert bft_client.get("/bft/crypto/public-keys").status_code == 200

    signed = bft_client.post(
        "/bft/crypto/sign",
        json={
            "protocol": "HOTSTUFF",
            "message_kind": "VOTE",
            "source_node_id": 1,
            "target_node_id": 2,
            "body": {"proposal_id": "p1"},
        },
    )
    assert signed.status_code == 200
    message = signed.json()
    verified = bft_client.post("/bft/crypto/verify", json=message)
    assert verified.status_code == 200
    assert verified.json()["valid"] is True
    replay = bft_client.post("/bft/crypto/verify", json=message)
    assert replay.status_code == 200
    assert replay.json()["replay"] is True
    assert bft_client.delete("/bft/crypto").status_code == 200
