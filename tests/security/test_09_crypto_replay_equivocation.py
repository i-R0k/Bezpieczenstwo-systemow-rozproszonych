from __future__ import annotations

from copy import deepcopy

from vetclinic_api.bft.fault_injection.equivocation import EQUIVOCATION_DETECTOR


def _signed_vote(client) -> dict:
    assert client.post("/bft/crypto/demo-keys?total_nodes=6").status_code == 200
    response = client.post(
        "/bft/crypto/sign",
        json={
            "protocol": "HOTSTUFF",
            "message_kind": "VOTE",
            "source_node_id": 1,
            "body": {"proposal_id": "p1", "accepted": True},
        },
    )
    assert response.status_code == 200
    return response.json()


def _submit_operation(client) -> str:
    response = client.post("/bft/client/submit", json={"sender": "alice", "recipient": "bob", "amount": 1})
    assert response.status_code == 200
    return response.json()["operation_id"]


def _proposal(client) -> tuple[str, str, str]:
    op = _submit_operation(client)
    batch = client.post("/bft/narwhal/batches", json={"operation_ids": [op], "max_operations": 1}).json()["batch"]["batch_id"]
    assert client.post(f"/bft/narwhal/batches/{batch}/certify-demo").status_code == 200
    proposal = client.post("/bft/hotstuff/proposals", json={"batch_id": batch})
    assert proposal.status_code == 200
    return op, batch, proposal.json()["proposal_id"]


def test_crypto_rejects_tampering_and_replay(security_bft_client):
    signed = _signed_vote(security_bft_client)
    assert security_bft_client.post("/bft/crypto/verify", json=signed).json()["valid"] is True
    assert security_bft_client.post("/bft/crypto/verify", json=signed).json()["replay"] is True

    for mutator in [
        lambda msg: msg["payload"]["body"].update({"accepted": False}),
        lambda msg: msg.update({"nonce": "forged-nonce"}),
        lambda msg: msg["payload"].update({"source_node_id": 2}),
        lambda msg: msg.update({"public_key_b64": "forged-public-key"}),
    ]:
        tampered = _signed_vote(security_bft_client)
        mutator(tampered)
        result = security_bft_client.post("/bft/crypto/verify", json=tampered).json()
        assert result["valid"] is False

    unknown = _signed_vote(security_bft_client)
    unknown["payload"]["source_node_id"] = 99
    result = security_bft_client.post("/bft/crypto/verify", json=unknown).json()
    assert result["valid"] is False
    assert result["reason"] in {"unknown_public_key", "message_id_mismatch", "public_key_mismatch"}


def test_replay_vote_and_batch_ack_are_idempotent(security_bft_client):
    _, batch_id, proposal_id = _proposal(security_bft_client)
    assert security_bft_client.post(
        "/bft/faults/rules",
        json={"fault_type": "REPLAY", "protocol": "HOTSTUFF", "message_kind": "VOTE"},
    ).status_code == 200

    first = security_bft_client.post(f"/bft/hotstuff/proposals/{proposal_id}/vote", json={"voter_node_id": 1})
    second = security_bft_client.post(f"/bft/hotstuff/proposals/{proposal_id}/vote", json={"voter_node_id": 1})
    votes = security_bft_client.get(f"/bft/hotstuff/proposals/{proposal_id}/votes").json()["votes"]

    assert first.status_code == 200
    assert second.status_code == 409
    assert len(votes) == 1

    first_ack = security_bft_client.post(f"/bft/narwhal/batches/{batch_id}/ack", json={"node_id": 2})
    second_ack = security_bft_client.post(f"/bft/narwhal/batches/{batch_id}/ack", json={"node_id": 2})
    vertex = security_bft_client.get("/bft/narwhal/dag").json()["vertices"][0]

    assert first_ack.status_code == 200
    assert second_ack.status_code == 200
    assert vertex["ack_node_ids"].count(2) == 1


def test_replay_recovery_does_not_create_duplicate_recovered_node_entries(security_bft_client):
    demo = security_bft_client.post("/bft/demo/run")
    checkpoint_id = demo.json()["checkpoint_id"]

    first = security_bft_client.post(f"/bft/recovery/nodes/3/recover-demo?checkpoint_id={checkpoint_id}")
    second = security_bft_client.post(f"/bft/recovery/nodes/3/recover-demo?checkpoint_id={checkpoint_id}")
    status = security_bft_client.get("/bft/recovery/status").json()

    assert first.status_code == 200
    assert second.status_code == 200
    assert len([node for node in status["recovered_nodes"] if node["node_id"] == 3]) == 1


def test_equivocation_detector_attack_cases_and_no_double_commit(security_bft_client):
    assert EQUIVOCATION_DETECTOR.record_proposal(1, 1, None, "p1", "block-a") is False
    assert EQUIVOCATION_DETECTOR.record_proposal(1, 1, None, "p2", "block-b") is True
    assert EQUIVOCATION_DETECTOR.record_proposal(2, 1, None, "p3", "block-c") is False
    assert EQUIVOCATION_DETECTOR.record_proposal(1, 2, None, "p4", "block-d") is False

    assert len(EQUIVOCATION_DETECTOR.list_conflicts()) == 1

    _, _, proposal_id = _proposal(security_bft_client)
    assert security_bft_client.post(
        "/bft/faults/rules",
        json={"fault_type": "EQUIVOCATION", "protocol": "HOTSTUFF", "message_kind": "PROPOSAL"},
    ).status_code == 200
    # Existing detector state plus equivocation marker should be visible through router.
    conflicts = security_bft_client.get("/bft/faults/equivocation/conflicts").json()["conflicts"]
    assert conflicts

    qc = security_bft_client.post(f"/bft/hotstuff/proposals/{proposal_id}/form-qc-demo").json()["qc_id"]
    assert security_bft_client.post(f"/bft/hotstuff/qc/{qc}/commit").status_code == 200
    assert security_bft_client.post(f"/bft/hotstuff/qc/{qc}/commit").status_code == 409
    assert len(security_bft_client.get("/bft/hotstuff/commits").json()["commits"]) == 1

