from __future__ import annotations


def test_list_limit_too_large_is_rejected(security_bft_client):
    response = security_bft_client.get("/bft/operations?limit=1000001")

    assert response.status_code == 422


def test_batch_max_operations_too_large_is_rejected(security_bft_client):
    response = security_bft_client.post(
        "/bft/narwhal/batches",
        json={"max_operations": 1000001},
    )

    assert response.status_code == 422


def test_deep_payload_does_not_return_500(security_bft_client):
    nested = value = {}
    for _ in range(50):
        value["child"] = {}
        value = value["child"]

    response = security_bft_client.post(
        "/bft/client/submit",
        json={"sender": "alice", "recipient": "bob", "amount": 1, "payload": nested},
    )

    assert response.status_code != 500


def test_repeated_operation_submit_keeps_store_count_consistent(security_bft_client):
    for index in range(100):
        response = security_bft_client.post(
            "/bft/client/submit",
            json={
                "sender": f"alice-{index}",
                "recipient": "bob",
                "amount": 1,
                "payload": {"index": index},
            },
        )
        assert response.status_code == 200

    status = security_bft_client.get("/bft/status")

    assert status.status_code == 200
    assert status.json()["operations"]["count"] == 100

