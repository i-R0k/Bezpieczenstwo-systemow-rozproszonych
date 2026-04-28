from __future__ import annotations

import sys
from pathlib import Path

import pytest

API_PATH = Path(__file__).resolve().parents[1] / "VetClinic" / "API"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from vetclinic_api.bft.common.events import EventLog  # noqa: E402
from vetclinic_api.bft.common.operations import (  # noqa: E402
    ClientOperationInput,
    InMemoryOperationStore,
)
from vetclinic_api.bft.common.types import OperationStatus, ProtocolName  # noqa: E402
from vetclinic_api.bft.narwhal.service import NarwhalService  # noqa: E402
from vetclinic_api.bft.narwhal.store import InMemoryNarwhalStore  # noqa: E402


def _service() -> tuple[NarwhalService, InMemoryOperationStore, EventLog]:
    operation_store = InMemoryOperationStore()
    event_log = EventLog()
    narwhal_store = InMemoryNarwhalStore(total_nodes=4)
    return (
        NarwhalService(operation_store, event_log, narwhal_store),
        operation_store,
        event_log,
    )


def _create_operation(operation_store: InMemoryOperationStore) -> str:
    operation = operation_store.create(
        ClientOperationInput(
            sender="alice",
            recipient="bob",
            amount=10.0,
            payload={"kind": "narwhal-test"},
        )
    )
    return operation.operation_id


def test_create_batch_from_received_operation_marks_batched() -> None:
    service, operation_store, _ = _service()
    operation_id = _create_operation(operation_store)

    response = service.create_batch_from_operations(
        author_node_id=1,
        total_nodes=4,
        operation_ids=[operation_id],
        max_operations=10,
    )

    assert response.batch.operation_ids == [operation_id]
    assert response.operations_marked == [operation_id]
    assert response.certificate is None
    assert operation_store.get(operation_id).status == OperationStatus.BATCHED


def test_create_batch_rejects_non_received_operation() -> None:
    service, operation_store, _ = _service()
    operation_id = _create_operation(operation_store)
    operation_store.transition(
        operation_id,
        OperationStatus.BATCHED,
        ProtocolName.NARWHAL,
        "already batched",
    )

    with pytest.raises(ValueError):
        service.create_batch_from_operations(
            author_node_id=1,
            total_nodes=4,
            operation_ids=[operation_id],
            max_operations=10,
        )


def test_acknowledge_batch_marks_available_after_quorum() -> None:
    service, operation_store, _ = _service()
    operation_id = _create_operation(operation_store)
    response = service.create_batch_from_operations(
        author_node_id=1,
        total_nodes=4,
        operation_ids=[operation_id],
        max_operations=10,
    )

    assert service.acknowledge_batch(response.batch.batch_id, 2, total_nodes=4) is None
    certificate = service.acknowledge_batch(
        response.batch.batch_id,
        3,
        total_nodes=4,
    )

    assert certificate is not None
    assert certificate.available is True
    assert operation_store.get(operation_id).status == OperationStatus.AVAILABLE


def test_certify_batch_locally_creates_certificate_and_available() -> None:
    service, operation_store, _ = _service()
    operation_id = _create_operation(operation_store)
    response = service.create_batch_from_operations(
        author_node_id=1,
        total_nodes=4,
        operation_ids=[operation_id],
        max_operations=10,
    )

    certificate = service.certify_batch_locally(response.batch.batch_id, total_nodes=4)

    assert certificate is not None
    assert certificate.ack_node_ids == [1, 2, 3]
    assert operation_store.get(operation_id).status == OperationStatus.AVAILABLE


def test_event_log_contains_narwhal_events() -> None:
    service, operation_store, event_log = _service()
    operation_id = _create_operation(operation_store)
    response = service.create_batch_from_operations(
        author_node_id=1,
        total_nodes=4,
        operation_ids=[operation_id],
        max_operations=10,
    )

    service.certify_batch_locally(response.batch.batch_id, total_nodes=4)

    messages = [event.message for event in event_log.list(limit=100)]
    assert "batch_created" in messages
    assert "batch_acknowledged" in messages
    assert "batch_certified" in messages
    assert "operation_available" in messages
