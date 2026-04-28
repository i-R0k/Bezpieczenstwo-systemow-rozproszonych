from __future__ import annotations

import pytest

from vetclinic_api.bft.common.types import NodeStatus, OperationStatus
from vetclinic_api.bft.hotstuff.service import HotStuffService
from vetclinic_api.bft.narwhal.service import NarwhalService


def _commit_operation(operation_store, event_log, narwhal_store, hotstuff_store, sample_input):
    narwhal = NarwhalService(operation_store, event_log, narwhal_store)
    hotstuff = HotStuffService(operation_store, event_log, narwhal_store, hotstuff_store)
    operation = operation_store.create(sample_input)
    batch = narwhal.create_batch_from_operations(1, 6, [operation.operation_id], 1).batch
    narwhal.certify_batch_locally(batch.batch_id, 6)
    hotstuff.run_hotstuff_demo_for_operation(operation.operation_id, 1, 6)
    assert operation_store.get(operation.operation_id).status == OperationStatus.COMMITTED
    return operation


@pytest.mark.bft
@pytest.mark.contract
def test_checkpoint_snapshot_certificate_and_recovery_flow(
    operation_store,
    event_log,
    narwhal_store,
    hotstuff_store,
    checkpoint_service,
    checkpoint_store,
    recovery_service,
    swim_store,
    sample_operation_input,
):
    operation = _commit_operation(
        operation_store,
        event_log,
        narwhal_store,
        hotstuff_store,
        sample_operation_input,
    )
    snapshot = checkpoint_service.create_snapshot(node_id=1)
    assert snapshot.operation_ids == [operation.operation_id]
    assert snapshot.state_hash

    certificate = checkpoint_service.certify_snapshot(snapshot.snapshot_id, total_nodes=6)
    assert certificate.valid is True
    assert certificate.quorum_size == 3
    assert checkpoint_store.latest_certificate() == certificate

    swim_store.bootstrap_from_config(1, "http://node1:8000", ["http://node2:8000"])
    swim_store.mark_dead(2)
    request = recovery_service.request_state_transfer(2, certificate.checkpoint_id)
    assert swim_store.get_member(2).status == NodeStatus.RECOVERING
    response = recovery_service.build_state_transfer_response(request)
    assert response.state_hash == snapshot.state_hash

    result = recovery_service.apply_state_transfer(request)
    assert result.status == "RECOVERED"
    assert result.applied_state_hash == snapshot.state_hash
    assert swim_store.get_member(2).status == NodeStatus.ALIVE
    messages = {event.message for event in event_log.list()}
    assert {
        "checkpoint_snapshot_created",
        "checkpoint_certificate_formed",
        "state_transfer_requested",
        "state_transfer_applied",
    } <= messages


@pytest.mark.bft
@pytest.mark.contract
def test_checkpoint_recovery_router_contract(bft_client):
    operation = bft_client.post(
        "/bft/client/submit",
        json={"sender": "alice", "recipient": "bob", "amount": 1},
    ).json()
    bft_client.post(f"/bft/operations/{operation['operation_id']}/run-demo")
    snapshot = bft_client.post("/bft/checkpointing/snapshots").json()
    certificate = bft_client.post(
        f"/bft/checkpointing/snapshots/{snapshot['snapshot_id']}/certify"
    ).json()
    bft_client.post("/bft/swim/bootstrap")
    bft_client.put("/bft/swim/members/2/dead")
    transfer = bft_client.post(
        "/bft/recovery/state-transfer",
        json={"node_id": 2, "checkpoint_id": certificate["checkpoint_id"]},
    )
    assert transfer.status_code == 200
    assert bft_client.post("/bft/recovery/state-transfer/2/response").status_code == 200
    result = bft_client.post("/bft/recovery/nodes/2/apply")
    assert result.status_code == 200
    assert result.json()["status"] == "RECOVERED"
    assert bft_client.get("/bft/checkpointing/status").status_code == 200
    assert bft_client.get("/bft/recovery/status").status_code == 200
