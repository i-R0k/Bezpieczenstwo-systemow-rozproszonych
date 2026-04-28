from __future__ import annotations

import pytest

from vetclinic_api.bft.common.types import OperationStatus, ProtocolName
from vetclinic_api.bft.hotstuff.service import HotStuffService
from vetclinic_api.bft.narwhal.service import NarwhalService


EXPECTED = [
    "RECEIVED",
    "BATCHED",
    "AVAILABLE",
    "PROPOSED",
    "VOTED",
    "QC_FORMED",
    "COMMITTED",
    "EXECUTED",
]


@pytest.mark.bft
@pytest.mark.integration
def test_full_service_pipeline(
    operation_store,
    event_log,
    narwhal_store,
    hotstuff_store,
    sample_operation_input,
):
    narwhal = NarwhalService(operation_store, event_log, narwhal_store)
    hotstuff = HotStuffService(operation_store, event_log, narwhal_store, hotstuff_store)
    operation = operation_store.create(sample_operation_input)
    batch = narwhal.create_batch_from_operations(1, 6, [operation.operation_id], 1).batch
    narwhal.certify_batch_locally(batch.batch_id, 6)
    hotstuff.run_hotstuff_demo_for_operation(operation.operation_id, 1, 6)
    operation_store.transition(
        operation.operation_id,
        OperationStatus.EXECUTED,
        ProtocolName.HOTSTUFF,
        "execute",
    )
    trace = operation_store.trace(operation.operation_id)
    assert trace.operation.status == OperationStatus.EXECUTED
    assert [item.to_status.value for item in trace.transitions] == EXPECTED


@pytest.mark.bft
@pytest.mark.integration
def test_full_router_pipeline(bft_client):
    response = bft_client.post(
        "/bft/client/submit",
        json={"sender": "alice", "recipient": "bob", "amount": 1},
    )
    operation_id = response.json()["operation_id"]
    demo = bft_client.post(f"/bft/operations/{operation_id}/run-demo")
    assert demo.status_code == 200
    trace = bft_client.get(f"/bft/operations/{operation_id}/trace").json()
    assert trace["operation"]["status"] == "EXECUTED"
    assert [item["to_status"] for item in trace["transitions"]] == EXPECTED


@pytest.mark.bft
@pytest.mark.integration
def test_swim_blocks_consensus_router(bft_client):
    bft_client.post("/bft/swim/bootstrap")
    bft_client.put("/bft/swim/members/3/dead")
    operation = bft_client.post(
        "/bft/client/submit",
        json={"sender": "alice", "recipient": "bob", "amount": 1},
    ).json()
    batch = bft_client.post(
        "/bft/narwhal/batches",
        json={"operation_ids": [operation["operation_id"]]},
    ).json()["batch"]
    bft_client.post(f"/bft/narwhal/batches/{batch['batch_id']}/certify-demo")
    proposal = bft_client.post(
        "/bft/hotstuff/proposals",
        json={"batch_id": batch["batch_id"], "proposer_node_id": 1},
    ).json()
    dead_vote = bft_client.post(
        f"/bft/hotstuff/proposals/{proposal['proposal_id']}/vote",
        json={"voter_node_id": 3},
    )
    assert dead_vote.status_code == 409
    live_vote = bft_client.post(
        f"/bft/hotstuff/proposals/{proposal['proposal_id']}/vote",
        json={"voter_node_id": 1},
    )
    assert live_vote.status_code == 200
