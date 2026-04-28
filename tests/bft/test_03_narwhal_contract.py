from __future__ import annotations

import pytest

from vetclinic_api.bft.common.types import OperationStatus
from vetclinic_api.bft.narwhal.models import BatchAck
from vetclinic_api.bft.narwhal.service import NarwhalService


def _narwhal(operation_store, event_log, narwhal_store):
    return NarwhalService(operation_store, event_log, narwhal_store)


def _operation(operation_store, sample_operation_input):
    return operation_store.create(sample_operation_input)


@pytest.mark.bft
@pytest.mark.contract
def test_narwhal_batch_creation_contract(
    operation_store,
    event_log,
    narwhal_store,
    sample_operation_input,
):
    service = _narwhal(operation_store, event_log, narwhal_store)
    operation = _operation(operation_store, sample_operation_input)
    response = service.create_batch_from_operations(1, 6, [operation.operation_id], 10)
    batch = response.batch
    assert batch.batch_id
    assert batch.author_node_id == 1
    assert batch.operation_ids == [operation.operation_id]
    assert batch.payload_hash
    assert narwhal_store.get_batch(batch.batch_id) == batch
    assert operation_store.get(operation.operation_id).status == OperationStatus.BATCHED


@pytest.mark.bft
@pytest.mark.contract
def test_narwhal_empty_batch_rejected(narwhal_store):
    with pytest.raises(ValueError):
        narwhal_store.create_batch(1, 1, [], [])


@pytest.mark.bft
@pytest.mark.contract
def test_narwhal_dag_contract(narwhal_store):
    first = narwhal_store.create_batch(1, 1, ["op-1"], [])
    second = narwhal_store.create_batch(1, 2, ["op-2"], narwhal_store.get_tips())
    dag = narwhal_store.get_dag()
    first_vertex = next(v for v in dag.vertices if v.batch.batch_id == first.batch_id)
    assert dag.tips == [second.batch_id]
    assert first_vertex.children == [second.batch_id]
    assert dag.total_batches == 2


@pytest.mark.bft
@pytest.mark.contract
def test_narwhal_ack_certificate_contract(narwhal_store):
    batch = narwhal_store.create_batch(1, 1, ["op-1"], [])
    assert narwhal_store.add_ack(BatchAck(batch_id=batch.batch_id, node_id=1, accepted=True)) is None
    assert narwhal_store.add_ack(BatchAck(batch_id=batch.batch_id, node_id=1, accepted=True)) is None
    assert len(narwhal_store.get_dag().vertices[0].ack_node_ids) == 1
    assert narwhal_store.add_ack(BatchAck(batch_id=batch.batch_id, node_id=2, accepted=True)) is None
    cert = narwhal_store.add_ack(BatchAck(batch_id=batch.batch_id, node_id=3, accepted=True))
    assert cert is not None
    assert cert.available is True
    with pytest.raises(KeyError):
        narwhal_store.add_ack(BatchAck(batch_id="missing", node_id=1, accepted=True))


@pytest.mark.bft
@pytest.mark.contract
def test_narwhal_availability_trace_and_events(
    operation_store,
    event_log,
    narwhal_store,
    sample_operation_input,
):
    service = _narwhal(operation_store, event_log, narwhal_store)
    operation = _operation(operation_store, sample_operation_input)
    response = service.create_batch_from_operations(1, 6, [operation.operation_id], 10)
    service.certify_batch_locally(response.batch.batch_id, 6)
    assert operation_store.get(operation.operation_id).status == OperationStatus.AVAILABLE
    statuses = [item.to_status for item in operation_store.trace(operation.operation_id).transitions]
    assert OperationStatus.BATCHED in statuses
    assert OperationStatus.AVAILABLE in statuses
    messages = [event.message for event in event_log.list()]
    assert {"batch_created", "batch_acknowledged", "batch_certified"} <= set(messages)


@pytest.mark.bft
@pytest.mark.contract
def test_narwhal_router_contract(bft_client):
    op = bft_client.post(
        "/bft/client/submit",
        json={"sender": "alice", "recipient": "bob", "amount": 1.0},
    ).json()
    created = bft_client.post("/bft/narwhal/batches", json={"operation_ids": [op["operation_id"]]})
    assert created.status_code == 200
    batch_id = created.json()["batch"]["batch_id"]
    assert bft_client.get("/bft/narwhal/batches").status_code == 200
    assert bft_client.get(f"/bft/narwhal/batches/{batch_id}").status_code == 200
    assert bft_client.post(f"/bft/narwhal/batches/{batch_id}/certify-demo").status_code == 200
    assert bft_client.get(f"/bft/narwhal/batches/{batch_id}/certificate").status_code == 200
    assert bft_client.get("/bft/narwhal/dag").status_code == 200
