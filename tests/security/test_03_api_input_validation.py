from __future__ import annotations


def test_client_submit_rejects_invalid_business_fields(security_bft_client):
    assert security_bft_client.post(
        "/bft/client/submit",
        json={"sender": "alice", "recipient": "bob", "amount": -1},
    ).status_code in {400, 422, 409}
    assert security_bft_client.post(
        "/bft/client/submit",
        json={"sender": "", "recipient": "bob", "amount": 1},
    ).status_code in {400, 422}
    assert security_bft_client.post(
        "/bft/client/submit",
        json={"sender": "alice", "recipient": "", "amount": 1},
    ).status_code in {400, 422}


def test_client_submit_large_or_deep_payload_is_controlled(security_bft_client):
    large_payload = {"blob": "x" * 70_000}
    large = security_bft_client.post(
        "/bft/client/submit",
        json={"sender": "alice", "recipient": "bob", "amount": 1, "payload": large_payload},
    )

    nested = value = {}
    for _ in range(40):
        value["child"] = {}
        value = value["child"]
    deep = security_bft_client.post(
        "/bft/client/submit",
        json={"sender": "alice", "recipient": "bob", "amount": 1, "payload": nested},
    )

    assert large.status_code != 500
    assert deep.status_code != 500


def test_narwhal_batch_limits_are_validated(security_bft_client):
    assert security_bft_client.post(
        "/bft/narwhal/batches",
        json={"max_operations": 0},
    ).status_code in {400, 422, 409}
    assert security_bft_client.post(
        "/bft/narwhal/batches",
        json={"max_operations": 10_000},
    ).status_code != 500


def test_fault_rule_validation_rejects_invalid_values(security_bft_client):
    base = {"fault_type": "DROP", "protocol": "HOTSTUFF", "message_kind": "VOTE"}
    assert security_bft_client.post(
        "/bft/faults/rules",
        json={**base, "probability": -0.1},
    ).status_code in {400, 422}
    assert security_bft_client.post(
        "/bft/faults/rules",
        json={**base, "probability": 1.1},
    ).status_code in {400, 422}
    assert security_bft_client.post(
        "/bft/faults/rules",
        json={**base, "delay_ms": -1},
    ).status_code in {400, 422}


def test_partition_and_query_validation(security_bft_client):
    partition = security_bft_client.post(
        "/bft/faults/partitions",
        json={"groups": [[1, 2], [2, 3]]},
    )
    limit = security_bft_client.get("/bft/operations?limit=-1")

    assert partition.status_code in {400, 422}
    assert limit.status_code == 422


def test_unknown_enums_are_rejected(security_bft_client):
    response = security_bft_client.post(
        "/bft/faults/rules",
        json={
            "fault_type": "UNKNOWN_FAULT",
            "protocol": "UNKNOWN_PROTOCOL",
            "message_kind": "UNKNOWN_KIND",
        },
    )

    assert response.status_code == 422

