from __future__ import annotations

import sys
from pathlib import Path

import pytest

API_PATH = Path(__file__).resolve().parents[1] / "VetClinic" / "API"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from vetclinic_api.bft.hotstuff.models import HotStuffBlock, HotStuffVote, TimeoutVote  # noqa: E402
from vetclinic_api.bft.hotstuff.store import (  # noqa: E402
    InMemoryHotStuffStore,
    build_block_id,
    stable_hash,
)


def _block(batch_id: str = "batch-1") -> HotStuffBlock:
    block_id = build_block_id(
        view=0,
        height=1,
        proposer_node_id=1,
        batch_id=batch_id,
        parent_block_id=None,
        justify_qc_id=None,
        payload_hash="payload-hash",
    )
    return HotStuffBlock(
        block_id=block_id,
        view=0,
        height=1,
        proposer_node_id=1,
        batch_id=batch_id,
        payload_hash="payload-hash",
    )


def _vote(proposal_id: str, block_id: str, voter: int) -> HotStuffVote:
    return HotStuffVote(
        vote_id=stable_hash(
            {
                "proposal_id": proposal_id,
                "block_id": block_id,
                "voter_node_id": voter,
            }
        ),
        proposal_id=proposal_id,
        block_id=block_id,
        voter_node_id=voter,
        accepted=True,
        view=0,
    )


def test_create_proposal() -> None:
    store = InMemoryHotStuffStore(total_nodes=4)
    proposal = store.create_proposal(_block(), batch_certificate_id="batch-1")

    assert proposal.proposal_id
    assert proposal.block.batch_id == "batch-1"
    assert store.get_proposal(proposal.proposal_id) == proposal


def test_vote_is_idempotent_for_same_voter() -> None:
    store = InMemoryHotStuffStore(total_nodes=4)
    proposal = store.create_proposal(_block(), batch_certificate_id="batch-1")

    assert store.add_vote(_vote(proposal.proposal_id, proposal.block.block_id, 1), 4) is None
    assert store.add_vote(_vote(proposal.proposal_id, proposal.block.block_id, 1), 4) is None

    assert len(store.get_votes(proposal.proposal_id)) == 1


def test_qc_forms_only_after_quorum() -> None:
    store = InMemoryHotStuffStore(total_nodes=4)
    proposal = store.create_proposal(_block(), batch_certificate_id="batch-1")

    assert store.add_vote(_vote(proposal.proposal_id, proposal.block.block_id, 1), 4) is None
    assert store.add_vote(_vote(proposal.proposal_id, proposal.block.block_id, 2), 4) is None
    qc = store.add_vote(_vote(proposal.proposal_id, proposal.block.block_id, 3), 4)

    assert qc is not None
    assert qc.valid is True
    assert qc.voter_node_ids == [1, 2, 3]
    assert store.current_view().high_qc_id == qc.qc_id
    assert store.current_view().locked_qc_id == qc.qc_id


def test_commit_requires_qc() -> None:
    store = InMemoryHotStuffStore(total_nodes=4)

    with pytest.raises(KeyError):
        store.commit("missing-qc", ["op-1"])


def test_cannot_commit_same_block_twice() -> None:
    store = InMemoryHotStuffStore(total_nodes=4)
    proposal = store.create_proposal(_block(), batch_certificate_id="batch-1")
    for voter in [1, 2, 3]:
        qc = store.add_vote(_vote(proposal.proposal_id, proposal.block.block_id, voter), 4)

    assert qc is not None
    store.commit(qc.qc_id, ["op-1"])
    with pytest.raises(ValueError):
        store.commit(qc.qc_id, ["op-1"])


def test_view_change_increments_view_and_leader() -> None:
    store = InMemoryHotStuffStore(total_nodes=4)

    view = store.advance_view(total_nodes=4)

    assert view.view == 1
    assert view.leader_node_id == 2


def test_timeout_votes_form_certificate_after_quorum() -> None:
    store = InMemoryHotStuffStore(total_nodes=4)

    assert store.add_timeout_vote(TimeoutVote(node_id=1, view=0, reason="timeout"), 4) is None
    assert store.add_timeout_vote(TimeoutVote(node_id=2, view=0, reason="timeout"), 4) is None
    tc = store.add_timeout_vote(TimeoutVote(node_id=3, view=0, reason="timeout"), 4)

    assert tc is not None
    assert tc.voter_node_ids == [1, 2, 3]
    assert tc.quorum_size == 3


def test_clear_resets_store() -> None:
    store = InMemoryHotStuffStore(total_nodes=4)
    proposal = store.create_proposal(_block(), batch_certificate_id="batch-1")
    store.advance_view(total_nodes=4)

    store.clear()

    assert store.list_proposals() == []
    assert store.list_qcs() == []
    assert store.list_commits() == []
    assert store.current_view().view == 0
    with pytest.raises(KeyError):
        store.get_proposal(proposal.proposal_id)
