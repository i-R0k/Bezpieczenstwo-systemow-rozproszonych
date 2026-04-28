from __future__ import annotations

import pytest

from vetclinic_api.bft.common.types import FaultType, MessageKind, ProtocolName
from vetclinic_api.bft.fault_injection.models import FaultEvaluationContext


def _ctx(
    protocol=ProtocolName.NARWHAL,
    message_kind=MessageKind.BATCH,
    source=1,
    target=2,
):
    return FaultEvaluationContext(
        protocol=protocol,
        message_kind=message_kind,
        source_node_id=source,
        target_node_id=target,
        message_id="msg-1",
    )


@pytest.mark.bft
@pytest.mark.contract
def test_fault_evaluate_decisions_and_filters(fault_service, fault_store, event_log):
    assert fault_service.evaluate(_ctx()).injected_faults == []

    fault_store.create_rule(fault_type=FaultType.DROP, protocol=ProtocolName.NARWHAL)
    assert fault_service.evaluate(_ctx()).should_drop is True

    fault_store.clear()
    fault_store.create_rule(fault_type=FaultType.DELAY, delay_ms=150)
    decision = fault_service.evaluate(_ctx())
    assert decision.should_delay is True
    assert decision.delay_ms == 150

    fault_store.clear()
    for fault_type, attr in [
        (FaultType.DUPLICATE, "should_duplicate"),
        (FaultType.REPLAY, "should_replay"),
        (FaultType.EQUIVOCATION, "should_equivocate"),
    ]:
        fault_store.create_rule(fault_type=fault_type)
        assert getattr(fault_service.evaluate(_ctx()), attr) is True
        fault_store.clear()

    fault_store.create_rule(fault_type=FaultType.DROP, protocol=ProtocolName.HOTSTUFF)
    assert fault_service.evaluate(_ctx()).should_drop is False
    fault_store.create_rule(
        fault_type=FaultType.DROP,
        protocol=ProtocolName.NARWHAL,
        source_node_id=3,
    )
    assert fault_service.evaluate(_ctx(source=1)).should_drop is False
    fault_store.clear()
    fault_store.create_rule(fault_type=FaultType.DROP, target_node_id=9)
    assert fault_service.evaluate(_ctx(target=2)).should_drop is False
    fault_store.clear()
    fault_store.create_rule(fault_type=FaultType.DROP, message_kind=MessageKind.VOTE)
    assert fault_service.evaluate(_ctx(message_kind=MessageKind.BATCH)).should_drop is False

    fault_store.clear()
    fault_store.create_rule(fault_type=FaultType.DROP, probability=0.0)
    assert fault_service.evaluate(_ctx()).should_drop is False
    fault_store.create_rule(fault_type=FaultType.DROP, probability=1.0)
    assert fault_service.evaluate(_ctx()).should_drop is True
    assert "fault_injected" in {event.message for event in event_log.list()}


@pytest.mark.bft
@pytest.mark.contract
def test_fault_partitions(fault_service, fault_store):
    fault_store.create_partition([[1, 2], [3, 4]])
    assert fault_service.is_partition_blocked(1, 3) is True
    assert fault_service.is_partition_blocked(1, 2) is False
    assert fault_service.evaluate(_ctx(source=1, target=3)).blocked_by_partition is True
