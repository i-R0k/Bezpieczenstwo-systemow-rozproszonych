from __future__ import annotations

import pytest

from vetclinic_api.bft.common.types import FaultType, MessageKind, NodeStatus, ProtocolName
from vetclinic_api.bft.swim.models import SwimGossipUpdate
from vetclinic_api.bft.swim.service import SwimService


def _service(swim_store, event_log, fault_service):
    service = SwimService(swim_store, event_log, fault_service)
    service.bootstrap(1, "http://node1:8000", ["http://node2:8000", "http://node3:8000"])
    return service


@pytest.mark.bft
@pytest.mark.integration
def test_drop_and_partition_ping_drive_suspect_dead(
    swim_store,
    event_log,
    fault_service,
    fault_store,
):
    service = _service(swim_store, event_log, fault_service)
    fault_store.create_rule(
        fault_type=FaultType.DROP,
        protocol=ProtocolName.SWIM,
        message_kind=MessageKind.SWIM_PING,
    )
    assert service.ping(1, 2).status_after == NodeStatus.SUSPECT
    assert service.ping(1, 2).status_after == NodeStatus.DEAD

    fault_store.clear()
    service.mark_alive(2)
    fault_store.create_partition([[1], [2, 3]])
    assert service.ping(1, 2).status_after == NodeStatus.SUSPECT
    assert "fault_injected" in {event.message for event in event_log.list()}


@pytest.mark.bft
@pytest.mark.integration
def test_delay_ping_and_drop_gossip(swim_store, event_log, fault_service, fault_store):
    service = _service(swim_store, event_log, fault_service)
    fault_store.create_rule(
        fault_type=FaultType.DELAY,
        protocol=ProtocolName.SWIM,
        message_kind=MessageKind.SWIM_PING,
        delay_ms=250,
    )
    assert service.ping(1, 2).ack is not None
    delay_events = [
        event
        for event in event_log.list()
        if event.message == "swim_ping_delay_simulated"
    ]
    assert delay_events[-1].details["delay_ms"] == 250

    fault_store.clear()
    fault_store.create_rule(
        fault_type=FaultType.DROP,
        protocol=ProtocolName.SWIM,
        message_kind=MessageKind.SWIM_GOSSIP,
    )
    with pytest.raises(ValueError):
        service.gossip(
            1,
            [SwimGossipUpdate(node_id=2, status=NodeStatus.DEAD, incarnation=5, observed_by=1)],
        )
    assert swim_store.get_member(2).status == NodeStatus.ALIVE
