from __future__ import annotations

import pytest

from vetclinic_api.bft.common.types import FaultType, MessageKind, ProtocolName
from vetclinic_api.bft.hotstuff.service import HotStuffService
from vetclinic_api.bft.narwhal.service import NarwhalService


def _proposal(operation_store, event_log, narwhal_store, hotstuff_store, fault_service, sample_input):
    narwhal = NarwhalService(operation_store, event_log, narwhal_store, fault_service)
    hotstuff = HotStuffService(
        operation_store,
        event_log,
        narwhal_store,
        hotstuff_store,
        fault_service=fault_service,
    )
    operation = operation_store.create(sample_input)
    batch = narwhal.create_batch_from_operations(1, 6, [operation.operation_id], 1).batch
    narwhal.certify_batch_locally(batch.batch_id, 6)
    return hotstuff, hotstuff.create_proposal_from_batch(batch.batch_id, 1, 6)


@pytest.mark.bft
@pytest.mark.contract
def test_replay_guard_basic(replay_guard):
    assert replay_guard.check_and_mark("m1") is False
    assert replay_guard.check_and_mark("m1") is True
    replay_guard.clear()
    assert replay_guard.seen("m1") is False


@pytest.mark.bft
@pytest.mark.integration
def test_replay_vote_and_commit_do_not_duplicate_state(
    operation_store,
    event_log,
    narwhal_store,
    hotstuff_store,
    fault_service,
    fault_store,
    sample_operation_input,
):
    hotstuff, proposal = _proposal(
        operation_store,
        event_log,
        narwhal_store,
        hotstuff_store,
        fault_service,
        sample_operation_input,
    )
    fault_store.create_rule(
        fault_type=FaultType.REPLAY,
        protocol=ProtocolName.HOTSTUFF,
        message_kind=MessageKind.VOTE,
    )
    hotstuff.vote(proposal.proposal_id, 1, total_nodes=6)
    with pytest.raises(ValueError, match="replay_detected"):
        hotstuff.vote(proposal.proposal_id, 1, total_nodes=6)
    assert len(hotstuff_store.get_votes(proposal.proposal_id)) == 1

    fault_store.clear()
    qc = hotstuff.form_qc_demo(proposal.proposal_id, 6)
    fault_store.create_rule(
        fault_type=FaultType.REPLAY,
        protocol=ProtocolName.HOTSTUFF,
        message_kind=MessageKind.COMMIT,
    )
    hotstuff.commit(qc.qc_id)
    with pytest.raises(ValueError, match="replay_detected"):
        hotstuff.commit(qc.qc_id)
    assert len(hotstuff_store.list_commits()) == 1
