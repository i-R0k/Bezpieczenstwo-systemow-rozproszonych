from __future__ import annotations

import pytest

from vetclinic_api.bft.common.types import OperationStatus, ProtocolName


def _advance_full(store, operation_id: str) -> None:
    for status in [
        OperationStatus.BATCHED,
        OperationStatus.AVAILABLE,
        OperationStatus.PROPOSED,
        OperationStatus.VOTED,
        OperationStatus.QC_FORMED,
        OperationStatus.COMMITTED,
        OperationStatus.EXECUTED,
    ]:
        store.transition(operation_id, status, ProtocolName.HOTSTUFF, status.value)


@pytest.mark.bft
@pytest.mark.contract
def test_operation_creation_contract(operation_store, sample_operation_input):
    operation = operation_store.create(sample_operation_input)
    assert isinstance(operation.operation_id, str)
    assert operation.status == OperationStatus.RECEIVED
    assert operation.payload is not None


@pytest.mark.bft
@pytest.mark.contract
def test_valid_operation_transitions_and_trace(operation_store, sample_operation_input):
    operation = operation_store.create(sample_operation_input)
    _advance_full(operation_store, operation.operation_id)
    trace = operation_store.trace(operation.operation_id)
    assert trace.operation.status == OperationStatus.EXECUTED
    assert [item.to_status for item in trace.transitions] == [
        OperationStatus.RECEIVED,
        OperationStatus.BATCHED,
        OperationStatus.AVAILABLE,
        OperationStatus.PROPOSED,
        OperationStatus.VOTED,
        OperationStatus.QC_FORMED,
        OperationStatus.COMMITTED,
        OperationStatus.EXECUTED,
    ]
    assert all(item.timestamp for item in trace.transitions)


@pytest.mark.bft
@pytest.mark.contract
def test_invalid_operation_transitions(operation_store, sample_operation_input):
    operation = operation_store.create(sample_operation_input)
    with pytest.raises(ValueError):
        operation_store.transition(
            operation.operation_id,
            OperationStatus.COMMITTED,
            ProtocolName.HOTSTUFF,
            "invalid",
        )
    operation_store.transition(
        operation.operation_id,
        OperationStatus.BATCHED,
        ProtocolName.NARWHAL,
        "batched",
    )
    with pytest.raises(ValueError):
        operation_store.transition(
            operation.operation_id,
            OperationStatus.PROPOSED,
            ProtocolName.HOTSTUFF,
            "invalid",
        )


@pytest.mark.bft
@pytest.mark.contract
def test_terminal_failed_rejected_contract(operation_store, sample_operation_input):
    failed = operation_store.create(sample_operation_input)
    operation_store.transition(
        failed.operation_id,
        OperationStatus.FAILED,
        ProtocolName.HOTSTUFF,
        "failed",
    )
    with pytest.raises(ValueError):
        operation_store.transition(
            failed.operation_id,
            OperationStatus.BATCHED,
            ProtocolName.NARWHAL,
            "invalid",
        )

    rejected = operation_store.create(sample_operation_input)
    for status in [
        OperationStatus.BATCHED,
        OperationStatus.AVAILABLE,
        OperationStatus.PROPOSED,
    ]:
        operation_store.transition(
            rejected.operation_id,
            status,
            ProtocolName.HOTSTUFF,
            status.value,
        )
    operation_store.transition(
        rejected.operation_id,
        OperationStatus.REJECTED,
        ProtocolName.HOTSTUFF,
        "rejected",
    )
    with pytest.raises(ValueError):
        operation_store.transition(
            rejected.operation_id,
            OperationStatus.COMMITTED,
            ProtocolName.HOTSTUFF,
            "invalid",
        )

    executed = operation_store.create(sample_operation_input)
    _advance_full(operation_store, executed.operation_id)
    with pytest.raises(ValueError):
        operation_store.transition(
            executed.operation_id,
            OperationStatus.FAILED,
            ProtocolName.HOTSTUFF,
            "too late",
        )
    with pytest.raises(ValueError):
        operation_store.transition(
            executed.operation_id,
            OperationStatus.REJECTED,
            ProtocolName.HOTSTUFF,
            "too late",
        )


@pytest.mark.bft
@pytest.mark.contract
def test_operation_router_contract(bft_client):
    response = bft_client.post(
        "/bft/client/submit",
        json={"sender": "alice", "recipient": "bob", "amount": 1.0},
    )
    assert response.status_code == 200
    operation = response.json()
    assert operation["status"] == "RECEIVED"
    operation_id = operation["operation_id"]
    assert bft_client.get(f"/bft/operations/{operation_id}").status_code == 200
    trace = bft_client.get(f"/bft/operations/{operation_id}/trace")
    assert trace.status_code == 200
    assert trace.json()["operation"]["operation_id"] == operation_id
    delete = bft_client.delete("/bft/operations")
    assert delete.status_code == 200
    assert bft_client.get(f"/bft/operations/{operation_id}").status_code == 404
