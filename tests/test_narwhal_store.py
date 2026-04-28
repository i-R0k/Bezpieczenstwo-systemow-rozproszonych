from __future__ import annotations

import sys
from pathlib import Path

import pytest

API_PATH = Path(__file__).resolve().parents[1] / "VetClinic" / "API"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from vetclinic_api.bft.narwhal.models import BatchAck  # noqa: E402
from vetclinic_api.bft.narwhal.store import InMemoryNarwhalStore  # noqa: E402


def test_create_batch_builds_payload_hash() -> None:
    store = InMemoryNarwhalStore(total_nodes=4)

    batch = store.create_batch(
        author_node_id=1,
        round=1,
        operation_ids=["op-1", "op-2"],
        parent_batch_ids=[],
    )

    assert batch.batch_id
    assert batch.payload_hash
    assert batch.operation_ids == ["op-1", "op-2"]
    assert store.get_batch(batch.batch_id) == batch


def test_create_batch_rejects_empty_operations() -> None:
    store = InMemoryNarwhalStore(total_nodes=4)

    with pytest.raises(ValueError):
        store.create_batch(
            author_node_id=1,
            round=1,
            operation_ids=[],
            parent_batch_ids=[],
        )


def test_dag_tips_update_after_batches() -> None:
    store = InMemoryNarwhalStore(total_nodes=4)
    first = store.create_batch(1, 1, ["op-1"], [])
    second = store.create_batch(1, 2, ["op-2"], store.get_tips())

    assert store.get_tips() == [second.batch_id]
    dag = store.get_dag()
    assert dag.total_batches == 2
    assert dag.tips == [second.batch_id]
    assert [vertex.batch.batch_id for vertex in dag.vertices] == [
        first.batch_id,
        second.batch_id,
    ]


def test_parent_children_are_updated() -> None:
    store = InMemoryNarwhalStore(total_nodes=4)
    parent = store.create_batch(1, 1, ["op-1"], [])
    child = store.create_batch(1, 2, ["op-2"], [parent.batch_id])

    dag = store.get_dag()
    parent_vertex = next(
        vertex for vertex in dag.vertices if vertex.batch.batch_id == parent.batch_id
    )
    child_vertex = next(
        vertex for vertex in dag.vertices if vertex.batch.batch_id == child.batch_id
    )
    assert parent_vertex.children == [child.batch_id]
    assert child_vertex.batch.parent_batch_ids == [parent.batch_id]


def test_ack_is_idempotent() -> None:
    store = InMemoryNarwhalStore(total_nodes=4)
    batch = store.create_batch(1, 1, ["op-1"], [])

    assert store.add_ack(BatchAck(batch_id=batch.batch_id, node_id=1, accepted=True)) is None
    assert store.add_ack(BatchAck(batch_id=batch.batch_id, node_id=1, accepted=True)) is None

    dag = store.get_dag()
    vertex = dag.vertices[0]
    assert vertex.ack_node_ids == [1]


def test_certificate_is_created_after_quorum() -> None:
    store = InMemoryNarwhalStore(total_nodes=4)
    batch = store.create_batch(1, 1, ["op-1"], [])

    assert store.add_ack(BatchAck(batch_id=batch.batch_id, node_id=1, accepted=True)) is None
    assert store.add_ack(BatchAck(batch_id=batch.batch_id, node_id=2, accepted=True)) is None

    certificate = store.add_ack(
        BatchAck(batch_id=batch.batch_id, node_id=3, accepted=True)
    )

    assert certificate is not None
    assert certificate.available is True
    assert certificate.ack_node_ids == [1, 2, 3]
    assert certificate.quorum_size == 3
    assert certificate.total_nodes == 4


def test_clear_removes_batches_and_tips() -> None:
    store = InMemoryNarwhalStore(total_nodes=4)
    batch = store.create_batch(1, 1, ["op-1"], [])
    store.add_ack(BatchAck(batch_id=batch.batch_id, node_id=1, accepted=True))

    store.clear()

    assert store.list_batches() == []
    assert store.get_tips() == []
    assert store.get_dag().total_batches == 0
    with pytest.raises(KeyError):
        store.get_batch(batch.batch_id)
