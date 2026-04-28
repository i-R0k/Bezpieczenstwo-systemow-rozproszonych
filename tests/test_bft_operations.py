from __future__ import annotations

import sys
from pathlib import Path

import pytest

API_PATH = Path(__file__).resolve().parents[1] / "VetClinic" / "API"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from vetclinic_api.bft.common.operations import (  # noqa: E402
    ClientOperationInput,
    InMemoryOperationStore,
)
from vetclinic_api.bft.common.types import OperationStatus, ProtocolName  # noqa: E402
from vetclinic_api.bft.common.events import EventLog  # noqa: E402
from vetclinic_api.bft.hotstuff.service import HotStuffService  # noqa: E402
from vetclinic_api.bft.hotstuff.store import InMemoryHotStuffStore  # noqa: E402
from vetclinic_api.bft.narwhal.service import NarwhalService  # noqa: E402
from vetclinic_api.bft.narwhal.store import InMemoryNarwhalStore  # noqa: E402


def _input() -> ClientOperationInput:
    return ClientOperationInput(
        sender="alice",
        recipient="bob",
        amount=10.5,
        payload={"kind": "demo"},
    )


def _advance_full_flow(store: InMemoryOperationStore, operation_id: str) -> None:
    store.transition(
        operation_id,
        OperationStatus.BATCHED,
        ProtocolName.NARWHAL,
        "batched",
    )
    store.transition(
        operation_id,
        OperationStatus.AVAILABLE,
        ProtocolName.NARWHAL,
        "available",
    )
    store.transition(
        operation_id,
        OperationStatus.PROPOSED,
        ProtocolName.HOTSTUFF,
        "proposed",
    )
    store.transition(
        operation_id,
        OperationStatus.VOTED,
        ProtocolName.HOTSTUFF,
        "voted",
    )
    store.transition(
        operation_id,
        OperationStatus.QC_FORMED,
        ProtocolName.HOTSTUFF,
        "qc formed",
    )
    store.transition(
        operation_id,
        OperationStatus.COMMITTED,
        ProtocolName.HOTSTUFF,
        "committed",
    )
    store.transition(
        operation_id,
        OperationStatus.EXECUTED,
        ProtocolName.HOTSTUFF,
        "executed",
    )


def test_create_operation() -> None:
    store = InMemoryOperationStore()
    operation = store.create(_input())

    assert operation.operation_id
    assert operation.sender == "alice"
    assert operation.recipient == "bob"
    assert operation.amount == 10.5
    assert operation.payload == {"kind": "demo"}
    assert operation.status == OperationStatus.RECEIVED


def test_full_operation_flow() -> None:
    store = InMemoryOperationStore()
    operation = store.create(_input())

    _advance_full_flow(store, operation.operation_id)

    assert store.get(operation.operation_id).status == OperationStatus.EXECUTED


def test_trace_contains_all_transitions() -> None:
    store = InMemoryOperationStore()
    operation = store.create(_input())

    _advance_full_flow(store, operation.operation_id)
    trace = store.trace(operation.operation_id)

    assert trace.operation.status == OperationStatus.EXECUTED
    assert [transition.to_status for transition in trace.transitions] == [
        OperationStatus.RECEIVED,
        OperationStatus.BATCHED,
        OperationStatus.AVAILABLE,
        OperationStatus.PROPOSED,
        OperationStatus.VOTED,
        OperationStatus.QC_FORMED,
        OperationStatus.COMMITTED,
        OperationStatus.EXECUTED,
    ]


def test_invalid_received_to_committed_transition_raises() -> None:
    store = InMemoryOperationStore()
    operation = store.create(_input())

    with pytest.raises(ValueError):
        store.transition(
            operation.operation_id,
            OperationStatus.COMMITTED,
            ProtocolName.HOTSTUFF,
            "invalid",
        )


@pytest.mark.parametrize(
    "target_status",
    [
        OperationStatus.RECEIVED,
        OperationStatus.BATCHED,
        OperationStatus.AVAILABLE,
        OperationStatus.PROPOSED,
        OperationStatus.VOTED,
        OperationStatus.QC_FORMED,
        OperationStatus.COMMITTED,
    ],
)
def test_failed_can_be_set_before_executed(target_status: OperationStatus) -> None:
    store = InMemoryOperationStore()
    operation = store.create(_input())
    flow = [
        OperationStatus.BATCHED,
        OperationStatus.AVAILABLE,
        OperationStatus.PROPOSED,
        OperationStatus.VOTED,
        OperationStatus.QC_FORMED,
        OperationStatus.COMMITTED,
    ]
    for status in flow:
        if target_status == OperationStatus.RECEIVED:
            break
        store.transition(
            operation.operation_id,
            status,
            ProtocolName.HOTSTUFF,
            f"advance to {status.value}",
        )
        if status == target_status:
            break

    failed = store.transition(
        operation.operation_id,
        OperationStatus.FAILED,
        ProtocolName.HOTSTUFF,
        "failed",
    )
    assert failed.status == OperationStatus.FAILED


def test_executed_operation_is_terminal() -> None:
    store = InMemoryOperationStore()
    operation = store.create(_input())
    _advance_full_flow(store, operation.operation_id)

    with pytest.raises(ValueError):
        store.transition(
            operation.operation_id,
            OperationStatus.FAILED,
            ProtocolName.HOTSTUFF,
            "too late",
        )


def test_clear_removes_operations() -> None:
    store = InMemoryOperationStore()
    operation = store.create(_input())

    assert store.get(operation.operation_id)
    store.clear()

    assert store.list() == []
    with pytest.raises(KeyError):
        store.get(operation.operation_id)


def test_real_narwhal_hotstuff_flow_reaches_executed_trace() -> None:
    operation_store = InMemoryOperationStore()
    event_log = EventLog()
    narwhal_store = InMemoryNarwhalStore(total_nodes=4)
    hotstuff_store = InMemoryHotStuffStore(total_nodes=4)
    narwhal = NarwhalService(operation_store, event_log, narwhal_store)
    hotstuff = HotStuffService(
        operation_store,
        event_log,
        narwhal_store,
        hotstuff_store,
    )
    operation = operation_store.create(_input())

    batch_response = narwhal.create_batch_from_operations(
        author_node_id=1,
        total_nodes=4,
        operation_ids=[operation.operation_id],
        max_operations=1,
    )
    narwhal.certify_batch_locally(batch_response.batch.batch_id, total_nodes=4)
    hotstuff.run_hotstuff_demo_for_operation(operation.operation_id, 1, 4)
    operation_store.transition(
        operation.operation_id,
        OperationStatus.EXECUTED,
        ProtocolName.HOTSTUFF,
        "executed",
    )

    trace = operation_store.trace(operation.operation_id)
    assert trace.operation.status == OperationStatus.EXECUTED
    assert [transition.to_status for transition in trace.transitions] == [
        OperationStatus.RECEIVED,
        OperationStatus.BATCHED,
        OperationStatus.AVAILABLE,
        OperationStatus.PROPOSED,
        OperationStatus.VOTED,
        OperationStatus.QC_FORMED,
        OperationStatus.COMMITTED,
        OperationStatus.EXECUTED,
    ]
