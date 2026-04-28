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
from vetclinic_api.bft.common.types import OperationStatus  # noqa: E402
from vetclinic_api.bft.hotstuff.service import HotStuffService  # noqa: E402
from vetclinic_api.bft.hotstuff.store import InMemoryHotStuffStore  # noqa: E402
from vetclinic_api.bft.narwhal.service import NarwhalService  # noqa: E402
from vetclinic_api.bft.narwhal.store import InMemoryNarwhalStore  # noqa: E402


def _services():
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
    return hotstuff, narwhal, operation_store, event_log


def _create_operation(operation_store: InMemoryOperationStore) -> str:
    operation = operation_store.create(
        ClientOperationInput(
            sender="alice",
            recipient="bob",
            amount=12.0,
            payload={"kind": "hotstuff-test"},
        )
    )
    return operation.operation_id


def _batch_operation(narwhal, operation_id: str):
    return narwhal.create_batch_from_operations(
        author_node_id=1,
        total_nodes=4,
        operation_ids=[operation_id],
        max_operations=1,
    )


def _available_batch(narwhal, operation_id: str):
    response = _batch_operation(narwhal, operation_id)
    narwhal.certify_batch_locally(response.batch.batch_id, total_nodes=4)
    return response.batch


def test_cannot_create_proposal_without_batch_certificate() -> None:
    hotstuff, narwhal, operation_store, _ = _services()
    operation_id = _create_operation(operation_store)
    response = _batch_operation(narwhal, operation_id)

    with pytest.raises(ValueError):
        hotstuff.create_proposal_from_batch(
            response.batch.batch_id,
            proposer_node_id=1,
            total_nodes=4,
        )


def test_create_proposal_marks_available_operation_proposed() -> None:
    hotstuff, narwhal, operation_store, _ = _services()
    operation_id = _create_operation(operation_store)
    batch = _available_batch(narwhal, operation_id)

    proposal = hotstuff.create_proposal_from_batch(batch.batch_id, 1, 4)

    assert proposal.block.batch_id == batch.batch_id
    assert operation_store.get(operation_id).status == OperationStatus.PROPOSED


def test_vote_marks_operation_voted() -> None:
    hotstuff, narwhal, operation_store, _ = _services()
    operation_id = _create_operation(operation_store)
    batch = _available_batch(narwhal, operation_id)
    proposal = hotstuff.create_proposal_from_batch(batch.batch_id, 1, 4)

    qc = hotstuff.vote(proposal.proposal_id, voter_node_id=1, total_nodes=4)

    assert qc is None
    assert operation_store.get(operation_id).status == OperationStatus.VOTED


def test_form_qc_demo_marks_operation_qc_formed() -> None:
    hotstuff, narwhal, operation_store, _ = _services()
    operation_id = _create_operation(operation_store)
    batch = _available_batch(narwhal, operation_id)
    proposal = hotstuff.create_proposal_from_batch(batch.batch_id, 1, 4)

    qc = hotstuff.form_qc_demo(proposal.proposal_id, total_nodes=4)

    assert qc.valid is True
    assert operation_store.get(operation_id).status == OperationStatus.QC_FORMED


def test_commit_marks_operation_committed() -> None:
    hotstuff, narwhal, operation_store, _ = _services()
    operation_id = _create_operation(operation_store)
    batch = _available_batch(narwhal, operation_id)
    proposal = hotstuff.create_proposal_from_batch(batch.batch_id, 1, 4)
    qc = hotstuff.form_qc_demo(proposal.proposal_id, total_nodes=4)

    commit = hotstuff.commit(qc.qc_id)

    assert commit.committed_operation_ids == [operation_id]
    assert operation_store.get(operation_id).status == OperationStatus.COMMITTED


def test_run_hotstuff_demo_for_operation_commits() -> None:
    hotstuff, narwhal, operation_store, _ = _services()
    operation_id = _create_operation(operation_store)
    _available_batch(narwhal, operation_id)

    result = hotstuff.run_hotstuff_demo_for_operation(operation_id, 1, 4)

    assert result["proposal"].block.batch_id
    assert result["qc"].valid is True
    assert result["commit"].committed_operation_ids == [operation_id]
    assert operation_store.get(operation_id).status == OperationStatus.COMMITTED


def test_event_log_contains_hotstuff_events() -> None:
    hotstuff, narwhal, operation_store, event_log = _services()
    operation_id = _create_operation(operation_store)
    _available_batch(narwhal, operation_id)

    hotstuff.run_hotstuff_demo_for_operation(operation_id, 1, 4)

    messages = [event.message for event in event_log.list(limit=100)]
    assert "hotstuff_proposal_created" in messages
    assert "hotstuff_vote_recorded" in messages
    assert "hotstuff_qc_formed" in messages
    assert "hotstuff_block_committed" in messages
