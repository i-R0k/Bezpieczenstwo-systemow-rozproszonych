from __future__ import annotations

import pytest

from vetclinic_api.bft.common.types import OperationStatus
from vetclinic_api.bft.hotstuff.models import TimeoutVote
from vetclinic_api.bft.hotstuff.service import HotStuffService
from vetclinic_api.bft.hotstuff.store import HOTSTUFF_STORE
from vetclinic_api.bft.narwhal.service import NarwhalService


def _stack(operation_store, event_log, narwhal_store, hotstuff_store):
    narwhal = NarwhalService(operation_store, event_log, narwhal_store)
    hotstuff = HotStuffService(operation_store, event_log, narwhal_store, hotstuff_store)
    return narwhal, hotstuff


def _available_batch(operation_store, event_log, narwhal_store, sample_operation_input):
    narwhal = NarwhalService(operation_store, event_log, narwhal_store)
    operation = operation_store.create(sample_operation_input)
    response = narwhal.create_batch_from_operations(1, 6, [operation.operation_id], 10)
    narwhal.certify_batch_locally(response.batch.batch_id, 6)
    return operation, response.batch


@pytest.mark.bft
@pytest.mark.contract
def test_hotstuff_proposal_contract(
    operation_store, event_log, narwhal_store, hotstuff_store, sample_operation_input
):
    operation = operation_store.create(sample_operation_input)
    narwhal, hotstuff = _stack(operation_store, event_log, narwhal_store, hotstuff_store)
    response = narwhal.create_batch_from_operations(1, 6, [operation.operation_id], 10)
    with pytest.raises(ValueError):
        hotstuff.create_proposal_from_batch(response.batch.batch_id, 1, 6)
    narwhal.certify_batch_locally(response.batch.batch_id, 6)
    proposal = hotstuff.create_proposal_from_batch(response.batch.batch_id, 1, 6)
    assert proposal.proposal_id
    assert proposal.block.block_id
    assert proposal.block.batch_id == response.batch.batch_id
    assert proposal.block.payload_hash == response.batch.payload_hash
    assert operation_store.get(operation.operation_id).status == OperationStatus.PROPOSED


@pytest.mark.bft
@pytest.mark.contract
def test_hotstuff_vote_qc_commit_contract(
    operation_store, event_log, narwhal_store, hotstuff_store, sample_operation_input
):
    operation, batch = _available_batch(operation_store, event_log, narwhal_store, sample_operation_input)
    hotstuff = HotStuffService(operation_store, event_log, narwhal_store, hotstuff_store)
    proposal = hotstuff.create_proposal_from_batch(batch.batch_id, 1, 6)
    qc = hotstuff.vote(proposal.proposal_id, 1, total_nodes=6)
    assert qc is None
    assert operation_store.get(operation.operation_id).status == OperationStatus.VOTED
    assert hotstuff.vote(proposal.proposal_id, 1, total_nodes=6) is None
    assert len(hotstuff_store.get_votes(proposal.proposal_id)) == 1
    qc = hotstuff.form_qc_demo(proposal.proposal_id, 6)
    assert qc.valid is True
    assert qc.voter_node_ids == [1, 2, 3]
    assert operation_store.get(operation.operation_id).status == OperationStatus.QC_FORMED
    with pytest.raises(KeyError):
        hotstuff_store.commit("missing", [operation.operation_id])
    commit = hotstuff.commit(qc.qc_id)
    assert commit.committed_operation_ids == [operation.operation_id]
    assert operation_store.get(operation.operation_id).status == OperationStatus.COMMITTED
    with pytest.raises(ValueError):
        hotstuff.commit(qc.qc_id)


@pytest.mark.bft
@pytest.mark.contract
def test_hotstuff_view_change_contract(hotstuff_store):
    assert hotstuff_store.current_view().view == 0
    view = hotstuff_store.advance_view(6)
    assert view.view == 1
    assert view.leader_node_id == 2
    assert hotstuff_store.add_timeout_vote(TimeoutVote(node_id=1, view=1, reason="timeout"), 6) is None
    assert hotstuff_store.add_timeout_vote(TimeoutVote(node_id=2, view=1, reason="timeout"), 6) is None
    tc = hotstuff_store.add_timeout_vote(TimeoutVote(node_id=3, view=1, reason="timeout"), 6)
    assert tc is not None


@pytest.mark.bft
@pytest.mark.contract
def test_hotstuff_router_contract(bft_client):
    op = bft_client.post(
        "/bft/client/submit",
        json={"sender": "alice", "recipient": "bob", "amount": 1.0},
    ).json()
    batch = bft_client.post("/bft/narwhal/batches", json={"operation_ids": [op["operation_id"]]}).json()["batch"]
    bft_client.post(f"/bft/narwhal/batches/{batch['batch_id']}/certify-demo")
    proposal = bft_client.post("/bft/hotstuff/proposals", json={"batch_id": batch["batch_id"]})
    assert proposal.status_code == 200
    proposal_id = proposal.json()["proposal_id"]
    qc = bft_client.post(f"/bft/hotstuff/proposals/{proposal_id}/form-qc-demo")
    assert qc.status_code == 200
    assert bft_client.post(f"/bft/hotstuff/qc/{qc.json()['qc_id']}/commit").status_code == 200
    assert bft_client.get("/bft/hotstuff/status").status_code == 200
    assert bft_client.post("/bft/hotstuff/view-change-demo").status_code == 200
