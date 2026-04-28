from __future__ import annotations


SECRET_MARKERS = ["private_key", "leader_priv_key", "bft_admin_token", "secret_key"]


def _assert_no_secret_markers(response_text: str) -> None:
    lowered = response_text.lower()
    for marker in SECRET_MARKERS:
        assert marker not in lowered


def test_rpc_node_info_does_not_expose_secrets(security_full_app_client):
    response = security_full_app_client.get("/rpc/node-info")

    assert response.status_code == 200
    _assert_no_secret_markers(response.text)


def test_rpc_block_endpoints_reject_invalid_payloads_without_500(security_full_app_client):
    forged = {"block": {"index": 999}, "hash": "forged", "signature": "forged"}

    propose = security_full_app_client.post("/rpc/propose_block", json=forged)
    commit = security_full_app_client.post("/rpc/commit_block", json=forged)

    assert propose.status_code != 500
    assert commit.status_code != 500
    _assert_no_secret_markers(propose.text)
    _assert_no_secret_markers(commit.text)


def test_chain_status_verify_and_mine_distributed_are_controlled(security_full_app_client):
    status = security_full_app_client.get("/chain/status")
    verify = security_full_app_client.get("/chain/verify")
    mine = security_full_app_client.post("/chain/mine_distributed")

    assert status.status_code in {200, 500}
    assert verify.status_code in {200, 400, 409, 500}
    assert mine.status_code != 500


def test_cluster_peers_does_not_expose_secrets(security_full_app_client):
    response = security_full_app_client.get("/peers")

    assert response.status_code == 200
    _assert_no_secret_markers(response.text)


def test_forged_signature_payload_to_transaction_receive_is_controlled(security_full_app_client):
    response = security_full_app_client.post(
        "/tx/receive",
        json={
            "id": "forged",
            "payload": {"sender": "alice", "recipient": "bob", "amount": "1"},
            "sender_pub": "forged",
            "signature": "forged",
            "timestamp": "2030-01-01T00:00:00",
        },
    )

    assert response.status_code != 500

