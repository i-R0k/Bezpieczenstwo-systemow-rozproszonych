from __future__ import annotations

import pytest

from vetclinic_api.bft.common.types import FaultType, MessageKind, ProtocolName
from vetclinic_api.bft.hotstuff.service import HotStuffService
from vetclinic_api.bft.narwhal.service import NarwhalService


@pytest.mark.bft
@pytest.mark.contract
def test_equivocation_detector_basic(equivocation_detector):
    assert equivocation_detector.record_proposal(0, 1, None, "p1", "b1") is False
    assert equivocation_detector.record_proposal(0, 1, None, "p2", "b1") is False
    assert equivocation_detector.record_proposal(1, 1, None, "p3", "b2") is False
    assert equivocation_detector.record_proposal(0, 2, None, "p4", "b2") is False
    assert equivocation_detector.record_proposal(0, 1, None, "p5", "b3") is True
    assert equivocation_detector.list_conflicts()


@pytest.mark.bft
@pytest.mark.integration
def test_equivocation_rule_records_conflict(
    operation_store,
    event_log,
    narwhal_store,
    hotstuff_store,
    fault_service,
    fault_store,
    equivocation_detector,
    sample_operation_input,
    bft_client,
):
    narwhal = NarwhalService(operation_store, event_log, narwhal_store, fault_service)
    hotstuff = HotStuffService(
        operation_store,
        event_log,
        narwhal_store,
        hotstuff_store,
        fault_service=fault_service,
    )
    operation = operation_store.create(sample_operation_input)
    batch = narwhal.create_batch_from_operations(1, 6, [operation.operation_id], 1).batch
    narwhal.certify_batch_locally(batch.batch_id, 6)
    fault_store.create_rule(
        fault_type=FaultType.EQUIVOCATION,
        protocol=ProtocolName.HOTSTUFF,
        message_kind=MessageKind.PROPOSAL,
    )
    hotstuff.create_proposal_from_batch(batch.batch_id, 1, 6)
    assert equivocation_detector.list_conflicts()
    assert bft_client.get("/bft/faults/equivocation/conflicts").status_code == 200
