from __future__ import annotations

import sys
from pathlib import Path

import pytest

API_PATH = Path(__file__).resolve().parents[1] / "VetClinic" / "API"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from vetclinic_api.bft.common.events import EventLog  # noqa: E402
from vetclinic_api.bft.common.operations import ClientOperationInput, InMemoryOperationStore  # noqa: E402
from vetclinic_api.bft.hotstuff.service import HotStuffService  # noqa: E402
from vetclinic_api.bft.hotstuff.store import InMemoryHotStuffStore  # noqa: E402
from vetclinic_api.bft.narwhal.service import NarwhalService  # noqa: E402
from vetclinic_api.bft.narwhal.store import InMemoryNarwhalStore  # noqa: E402
from vetclinic_api.bft.swim.service import SwimService  # noqa: E402
from vetclinic_api.bft.swim.store import InMemorySwimStore  # noqa: E402


def _stack():
    operation_store = InMemoryOperationStore()
    event_log = EventLog()
    narwhal_store = InMemoryNarwhalStore(total_nodes=4)
    hotstuff_store = InMemoryHotStuffStore(total_nodes=4)
    swim_store = InMemorySwimStore()
    swim = SwimService(swim_store, event_log)
    swim.bootstrap(
        1,
        "http://node1:8000",
        ["http://node2:8000", "http://node3:8000", "http://node4:8000"],
    )
    narwhal = NarwhalService(operation_store, event_log, narwhal_store)
    hotstuff = HotStuffService(
        operation_store,
        event_log,
        narwhal_store,
        hotstuff_store,
        swim_store,
    )
    operation = operation_store.create(
        ClientOperationInput(sender="a", recipient="b", amount=1.0)
    )
    batch_response = narwhal.create_batch_from_operations(
        1,
        4,
        [operation.operation_id],
        1,
    )
    narwhal.certify_batch_locally(batch_response.batch.batch_id, 4)
    return hotstuff, swim, batch_response.batch.batch_id


def test_dead_node_cannot_be_proposer() -> None:
    hotstuff, swim, batch_id = _stack()
    swim.mark_dead(2)

    with pytest.raises(ValueError):
        hotstuff.create_proposal_from_batch(batch_id, proposer_node_id=2, total_nodes=4)


def test_dead_node_cannot_vote() -> None:
    hotstuff, swim, batch_id = _stack()
    proposal = hotstuff.create_proposal_from_batch(batch_id, 1, 4)
    swim.mark_dead(2)

    with pytest.raises(ValueError):
        hotstuff.vote(proposal.proposal_id, voter_node_id=2, total_nodes=4)


def test_alive_node_can_vote() -> None:
    hotstuff, _, batch_id = _stack()
    proposal = hotstuff.create_proposal_from_batch(batch_id, 1, 4)

    qc = hotstuff.vote(proposal.proposal_id, voter_node_id=2, total_nodes=4)

    assert qc is None
