from __future__ import annotations


def _submit_operation(client) -> str:
    response = client.post(
        "/bft/client/submit",
        json={"sender": "alice", "recipient": "bob", "amount": 1, "payload": {"security": True}},
    )
    assert response.status_code == 200
    return response.json()["operation_id"]


def _create_batch(client, operation_id: str) -> str:
    response = client.post(
        "/bft/narwhal/batches",
        json={"operation_ids": [operation_id], "max_operations": 1},
    )
    assert response.status_code == 200
    return response.json()["batch"]["batch_id"]


def _certified_proposal(client) -> tuple[str, str, str]:
    operation_id = _submit_operation(client)
    batch_id = _create_batch(client, operation_id)
    certify = client.post(f"/bft/narwhal/batches/{batch_id}/certify-demo")
    assert certify.status_code == 200
    proposal = client.post("/bft/hotstuff/proposals", json={"batch_id": batch_id})
    assert proposal.status_code == 200
    return operation_id, batch_id, proposal.json()["proposal_id"]


def test_hotstuff_rejects_proposal_for_batch_without_certificate(security_bft_client):
    operation_id = _submit_operation(security_bft_client)
    batch_id = _create_batch(security_bft_client, operation_id)

    response = security_bft_client.post("/bft/hotstuff/proposals", json={"batch_id": batch_id})

    assert response.status_code == 409


def test_hotstuff_rejects_commit_without_qc_and_double_commit(security_bft_client):
    _, _, proposal_id = _certified_proposal(security_bft_client)

    missing_qc = security_bft_client.post("/bft/hotstuff/qc/not-a-qc/commit")
    qc = security_bft_client.post(f"/bft/hotstuff/proposals/{proposal_id}/form-qc-demo")
    first_commit = security_bft_client.post(f"/bft/hotstuff/qc/{qc.json()['qc_id']}/commit")
    second_commit = security_bft_client.post(f"/bft/hotstuff/qc/{qc.json()['qc_id']}/commit")

    assert missing_qc.status_code in {404, 409}
    assert first_commit.status_code == 200
    assert second_commit.status_code == 409


def test_dead_suspect_and_recovering_nodes_cannot_vote(security_bft_client):
    _, _, proposal_id = _certified_proposal(security_bft_client)
    assert security_bft_client.post("/bft/swim/bootstrap").status_code == 200

    checks = [
        ("/bft/swim/members/2/dead", 2),
        ("/bft/swim/members/3/suspect", 3),
        ("/bft/swim/members/4/recovering", 4),
    ]
    for mark_path, node_id in checks:
        assert security_bft_client.put(mark_path).status_code == 200
        vote = security_bft_client.post(
            f"/bft/hotstuff/proposals/{proposal_id}/vote",
            json={"voter_node_id": node_id, "accepted": True},
        )
        assert vote.status_code == 409


def test_drop_vote_fault_prevents_qc(security_bft_client):
    _, _, proposal_id = _certified_proposal(security_bft_client)
    rule = security_bft_client.post(
        "/bft/faults/rules",
        json={"fault_type": "DROP", "protocol": "HOTSTUFF", "message_kind": "VOTE", "probability": 1.0},
    )

    response = security_bft_client.post(f"/bft/hotstuff/proposals/{proposal_id}/form-qc-demo")

    assert rule.status_code == 200
    assert response.status_code == 409
    assert security_bft_client.get("/bft/hotstuff/status").json()["quorum_certificates"] == []


def test_network_partition_prevents_cross_group_quorum(security_bft_client):
    _, _, proposal_id = _certified_proposal(security_bft_client)
    partition = security_bft_client.post("/bft/faults/partitions", json={"groups": [[1, 2], [3, 4, 5, 6]]})

    response = security_bft_client.post(f"/bft/hotstuff/proposals/{proposal_id}/form-qc-demo")

    assert partition.status_code == 200
    assert response.status_code == 409
    assert security_bft_client.get("/bft/hotstuff/status").json()["quorum_certificates"] == []

