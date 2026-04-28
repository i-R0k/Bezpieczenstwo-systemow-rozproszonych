from __future__ import annotations

import pytest

from vetclinic_api.bft.common.types import FaultType, MessageKind, OperationStatus, ProtocolName
from vetclinic_api.bft.narwhal.service import NarwhalService


def _service(operation_store, event_log, narwhal_store, fault_service):
    return NarwhalService(operation_store, event_log, narwhal_store, fault_service)


@pytest.mark.bft
@pytest.mark.integration
def test_drop_batch_blocks_create_and_keeps_operation_received(
    operation_store,
    event_log,
    narwhal_store,
    fault_service,
    fault_store,
    sample_operation_input,
):
    service = _service(operation_store, event_log, narwhal_store, fault_service)
    operation = operation_store.create(sample_operation_input)
    fault_store.create_rule(
        fault_type=FaultType.DROP,
        protocol=ProtocolName.NARWHAL,
        message_kind=MessageKind.BATCH,
    )
    with pytest.raises(ValueError):
        service.create_batch_from_operations(1, 6, [operation.operation_id], 1)
    assert operation_store.get(operation.operation_id).status == OperationStatus.RECEIVED
    assert "narwhal_batch_dropped" in {event.message for event in event_log.list()}


@pytest.mark.bft
@pytest.mark.integration
def test_ack_drop_partition_and_duplicate_are_safe(
    operation_store,
    event_log,
    narwhal_store,
    fault_service,
    fault_store,
    sample_operation_input,
):
    service = _service(operation_store, event_log, narwhal_store, fault_service)
    operation = operation_store.create(sample_operation_input)
    batch = service.create_batch_from_operations(1, 6, [operation.operation_id], 1).batch

    fault_store.create_rule(
        fault_type=FaultType.DROP,
        protocol=ProtocolName.NARWHAL,
        message_kind=MessageKind.BATCH_ACK,
    )
    assert service.certify_batch_locally(batch.batch_id, 6) is None
    assert narwhal_store.get_certificate(batch.batch_id) is None

    fault_store.clear()
    fault_store.create_partition([[1], [2], [3, 4, 5, 6]])
    assert service.acknowledge_batch(batch.batch_id, 2, total_nodes=6) is None
    assert 2 not in narwhal_store.get_dag().vertices[0].ack_node_ids

    fault_store.clear()
    fault_store.create_rule(
        fault_type=FaultType.DUPLICATE,
        protocol=ProtocolName.NARWHAL,
        message_kind=MessageKind.BATCH_ACK,
    )
    service.acknowledge_batch(batch.batch_id, 3, total_nodes=6)
    service.acknowledge_batch(batch.batch_id, 3, total_nodes=6)
    assert narwhal_store.get_dag().vertices[0].ack_node_ids.count(3) == 1
    assert "fault_injected" in {event.message for event in event_log.list()}
