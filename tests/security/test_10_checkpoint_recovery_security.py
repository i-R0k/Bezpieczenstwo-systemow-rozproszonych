from __future__ import annotations


def _demo_checkpoint(client) -> tuple[str, str]:
    report = client.post("/bft/demo/run")
    assert report.status_code == 200
    return report.json()["operation_id"], report.json()["checkpoint_id"]


def test_state_transfer_requires_certified_checkpoint(security_bft_client):
    response = security_bft_client.post("/bft/recovery/state-transfer", json={"node_id": 3})

    assert response.status_code == 409


def test_recovery_with_unknown_checkpoint_is_rejected(security_bft_client):
    response = security_bft_client.post("/bft/recovery/nodes/3/recover-demo?checkpoint_id=missing")

    assert response.status_code in {404, 409}


def test_recovery_restores_node_hash_to_checkpoint_hash(security_bft_client):
    _, checkpoint_id = _demo_checkpoint(security_bft_client)
    checkpoint = security_bft_client.get(f"/bft/checkpointing/certificates/{checkpoint_id}").json()

    result = security_bft_client.post(f"/bft/recovery/nodes/4/recover-demo?checkpoint_id={checkpoint_id}")

    assert result.status_code == 200
    assert "corrupted-local-hash" != checkpoint["state_hash"]
    assert result.json()["applied_state_hash"] == checkpoint["state_hash"]


def test_checkpoint_with_insufficient_quorum_is_not_valid(security_bft_client):
    _demo_checkpoint(security_bft_client)
    snapshot = security_bft_client.post("/bft/checkpointing/snapshots").json()

    response = security_bft_client.post(
        f"/bft/checkpointing/snapshots/{snapshot['snapshot_id']}/certify",
        json={"signer_node_ids": [1]},
    )

    assert response.status_code == 409


def test_forged_checkpoint_certificate_is_not_accepted_by_router(security_bft_client):
    response = security_bft_client.get("/bft/checkpointing/certificates/forged-checkpoint")

    assert response.status_code == 404


def test_recovering_node_cannot_vote_or_propose_until_recovered(security_bft_client):
    _, checkpoint_id = _demo_checkpoint(security_bft_client)
    op = security_bft_client.post("/bft/client/submit", json={"sender": "alice", "recipient": "bob", "amount": 1}).json()["operation_id"]
    batch = security_bft_client.post("/bft/narwhal/batches", json={"operation_ids": [op], "max_operations": 1}).json()["batch"]["batch_id"]
    assert security_bft_client.post(f"/bft/narwhal/batches/{batch}/certify-demo").status_code == 200
    assert security_bft_client.put("/bft/swim/members/4/recovering").status_code == 200

    propose = security_bft_client.post("/bft/hotstuff/proposals", json={"batch_id": batch, "proposer_node_id": 4})
    proposal = security_bft_client.post("/bft/hotstuff/proposals", json={"batch_id": batch, "proposer_node_id": 1})
    vote = security_bft_client.post(
        f"/bft/hotstuff/proposals/{proposal.json()['proposal_id']}/vote",
        json={"voter_node_id": 4},
    )
    recovered = security_bft_client.post(f"/bft/recovery/nodes/4/recover-demo?checkpoint_id={checkpoint_id}")
    vote_after = security_bft_client.post(
        f"/bft/hotstuff/proposals/{proposal.json()['proposal_id']}/vote",
        json={"voter_node_id": 4},
    )

    assert propose.status_code == 409
    assert vote.status_code == 409
    assert recovered.status_code == 200
    assert vote_after.status_code == 200

