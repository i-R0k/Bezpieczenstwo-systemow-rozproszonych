from __future__ import annotations

import time


def _proposal(client) -> str:
    op = client.post("/bft/client/submit", json={"sender": "alice", "recipient": "bob", "amount": 1}).json()["operation_id"]
    batch = client.post("/bft/narwhal/batches", json={"operation_ids": [op], "max_operations": 1}).json()["batch"]["batch_id"]
    assert client.post(f"/bft/narwhal/batches/{batch}/certify-demo").status_code == 200
    proposal = client.post("/bft/hotstuff/proposals", json={"batch_id": batch})
    assert proposal.status_code == 200
    return proposal.json()["proposal_id"]


def test_drop_proposal_and_commit_return_controlled_conflicts(security_bft_client):
    op = security_bft_client.post("/bft/client/submit", json={"sender": "alice", "recipient": "bob", "amount": 1}).json()["operation_id"]
    batch = security_bft_client.post("/bft/narwhal/batches", json={"operation_ids": [op], "max_operations": 1}).json()["batch"]["batch_id"]
    assert security_bft_client.post(f"/bft/narwhal/batches/{batch}/certify-demo").status_code == 200
    assert security_bft_client.post(
        "/bft/faults/rules",
        json={"fault_type": "DROP", "protocol": "HOTSTUFF", "message_kind": "PROPOSAL"},
    ).status_code == 200
    assert security_bft_client.post("/bft/hotstuff/proposals", json={"batch_id": batch}).status_code == 409

    security_bft_client.delete("/bft/faults")
    proposal_id = _proposal(security_bft_client)
    qc = security_bft_client.post(f"/bft/hotstuff/proposals/{proposal_id}/form-qc-demo").json()["qc_id"]
    assert security_bft_client.post(
        "/bft/faults/rules",
        json={"fault_type": "DROP", "protocol": "HOTSTUFF", "message_kind": "COMMIT"},
    ).status_code == 200
    assert security_bft_client.post(f"/bft/hotstuff/qc/{qc}/commit").status_code == 409


def test_drop_swim_ping_moves_member_towards_suspect_or_dead(security_bft_client):
    assert security_bft_client.post("/bft/swim/bootstrap").status_code == 200
    assert security_bft_client.post(
        "/bft/faults/rules",
        json={"fault_type": "DROP", "protocol": "SWIM", "message_kind": "SWIM_PING"},
    ).status_code == 200

    response = security_bft_client.post("/bft/swim/ping/2")

    assert response.status_code == 200
    assert response.json()["status_after"] in {"SUSPECT", "DEAD"}


def test_delay_fault_is_simulated_without_real_sleep(security_bft_client):
    assert security_bft_client.post(
        "/bft/faults/rules",
        json={"fault_type": "DELAY", "protocol": "HOTSTUFF", "message_kind": "VOTE", "delay_ms": 5000},
    ).status_code == 200
    start = time.perf_counter()
    response = security_bft_client.post(
        "/bft/faults/evaluate",
        json={"protocol": "HOTSTUFF", "message_kind": "VOTE", "source_node_id": 1, "target_node_id": 2},
    )
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert response.json()["should_delay"] is True
    assert elapsed < 0.5


def test_duplicate_fault_keeps_ack_idempotent_and_probability_edges(security_bft_client):
    op = security_bft_client.post("/bft/client/submit", json={"sender": "alice", "recipient": "bob", "amount": 1}).json()["operation_id"]
    batch = security_bft_client.post("/bft/narwhal/batches", json={"operation_ids": [op], "max_operations": 1}).json()["batch"]["batch_id"]
    assert security_bft_client.post(
        "/bft/faults/rules",
        json={"fault_type": "DUPLICATE", "protocol": "NARWHAL", "message_kind": "BATCH_ACK"},
    ).status_code == 200
    assert security_bft_client.post(f"/bft/narwhal/batches/{batch}/ack", json={"node_id": 2}).status_code == 200
    assert security_bft_client.post(f"/bft/narwhal/batches/{batch}/ack", json={"node_id": 2}).status_code == 200
    vertex = security_bft_client.get("/bft/narwhal/dag").json()["vertices"][0]
    assert vertex["ack_node_ids"].count(2) == 1

    security_bft_client.delete("/bft/faults")
    zero = security_bft_client.post(
        "/bft/faults/rules",
        json={"fault_type": "DROP", "protocol": "HOTSTUFF", "message_kind": "VOTE", "probability": 0.0},
    ).json()
    decision_zero = security_bft_client.post(
        "/bft/faults/evaluate",
        json={"protocol": "HOTSTUFF", "message_kind": "VOTE"},
    ).json()
    security_bft_client.delete(f"/bft/faults/rules/{zero['rule_id']}")
    one = security_bft_client.post(
        "/bft/faults/rules",
        json={"fault_type": "DROP", "protocol": "HOTSTUFF", "message_kind": "VOTE", "probability": 1.0},
    )
    decision_one = security_bft_client.post(
        "/bft/faults/evaluate",
        json={"protocol": "HOTSTUFF", "message_kind": "VOTE"},
    ).json()

    assert decision_zero["should_drop"] is False
    assert one.status_code == 200
    assert decision_one["should_drop"] is True


def test_clear_faults_removes_rules_and_injected_faults(security_bft_client):
    assert security_bft_client.post(
        "/bft/faults/rules",
        json={"fault_type": "DROP", "protocol": "HOTSTUFF", "message_kind": "VOTE"},
    ).status_code == 200
    assert security_bft_client.post(
        "/bft/faults/evaluate",
        json={"protocol": "HOTSTUFF", "message_kind": "VOTE"},
    ).status_code == 200

    cleared = security_bft_client.delete("/bft/faults")
    status = security_bft_client.get("/bft/faults/status").json()

    assert cleared.status_code == 200
    assert status["rules"] == []
    assert status["injected_faults"] == []

