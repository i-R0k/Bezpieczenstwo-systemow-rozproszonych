from __future__ import annotations

import pytest

from vetclinic_api.bft.common.types import FaultType, MessageKind, ProtocolName
from vetclinic_api.bft.hotstuff.service import HotStuffService
from vetclinic_api.bft.narwhal.service import NarwhalService


def _available_batch(operation_store, event_log, narwhal_store, fault_service, sample_input):
    narwhal = NarwhalService(operation_store, event_log, narwhal_store, fault_service)
    operation = operation_store.create(sample_input)
    batch = narwhal.create_batch_from_operations(1, 6, [operation.operation_id], 1).batch
    narwhal.certify_batch_locally(batch.batch_id, 6)
    return batch


def _hotstuff(operation_store, event_log, narwhal_store, hotstuff_store, fault_service):
    return HotStuffService(
        operation_store,
        event_log,
        narwhal_store,
        hotstuff_store,
        fault_service=fault_service,
    )


@pytest.mark.bft
@pytest.mark.integration
def test_proposal_faults_block_hotstuff(
    operation_store,
    event_log,
    narwhal_store,
    hotstuff_store,
    fault_service,
    fault_store,
    sample_operation_input,
):
    batch = _available_batch(
        operation_store, event_log, narwhal_store, fault_service, sample_operation_input
    )
    hotstuff = _hotstuff(operation_store, event_log, narwhal_store, hotstuff_store, fault_service)
    fault_store.create_rule(
        fault_type=FaultType.DROP,
        protocol=ProtocolName.HOTSTUFF,
        message_kind=MessageKind.PROPOSAL,
    )
    with pytest.raises(ValueError):
        hotstuff.create_proposal_from_batch(batch.batch_id, 1, 6)
    fault_store.clear()
    fault_store.create_rule(
        fault_type=FaultType.LEADER_FAILURE,
        protocol=ProtocolName.HOTSTUFF,
        message_kind=MessageKind.PROPOSAL,
    )
    with pytest.raises(ValueError):
        hotstuff.create_proposal_from_batch(batch.batch_id, 1, 6)


@pytest.mark.bft
@pytest.mark.integration
def test_vote_commit_replay_partition_and_equivocation_faults(
    operation_store,
    event_log,
    narwhal_store,
    hotstuff_store,
    fault_service,
    fault_store,
    equivocation_detector,
    sample_operation_input,
):
    batch = _available_batch(
        operation_store, event_log, narwhal_store, fault_service, sample_operation_input
    )
    hotstuff = _hotstuff(operation_store, event_log, narwhal_store, hotstuff_store, fault_service)
    fault_store.create_rule(
        fault_type=FaultType.EQUIVOCATION,
        protocol=ProtocolName.HOTSTUFF,
        message_kind=MessageKind.PROPOSAL,
    )
    proposal = hotstuff.create_proposal_from_batch(batch.batch_id, 1, 6)
    assert equivocation_detector.list_conflicts()

    fault_store.clear()
    fault_store.create_rule(
        fault_type=FaultType.DROP,
        protocol=ProtocolName.HOTSTUFF,
        message_kind=MessageKind.VOTE,
    )
    with pytest.raises(ValueError):
        hotstuff.vote(proposal.proposal_id, 1, total_nodes=6)
    assert hotstuff_store.get_qc_for_proposal(proposal.proposal_id) is None

    fault_store.clear()
    fault_store.create_partition([[1], [2], [3, 4, 5, 6]])
    with pytest.raises(ValueError):
        hotstuff.vote(proposal.proposal_id, 2, total_nodes=6)

    fault_store.clear()
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
        fault_type=FaultType.DROP,
        protocol=ProtocolName.HOTSTUFF,
        message_kind=MessageKind.COMMIT,
    )
    with pytest.raises(ValueError):
        hotstuff.commit(qc.qc_id)
