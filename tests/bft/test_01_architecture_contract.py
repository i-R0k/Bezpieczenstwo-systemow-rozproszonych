from __future__ import annotations

import importlib

import pytest

from vetclinic_api.bft.common.events import EventLog, ProtocolEvent
from vetclinic_api.bft.common.quorum import (
    describe_quorum,
    fault_tolerance,
    has_quorum,
    quorum_size,
)
from vetclinic_api.bft.common.types import (
    FaultType,
    MessageKind,
    OperationStatus,
    ProtocolName,
    NodeStatus,
)


@pytest.mark.bft
@pytest.mark.contract
def test_bft_import_contract():
    for module in [
        "vetclinic_api.bft.common.types",
        "vetclinic_api.bft.common.events",
        "vetclinic_api.bft.common.quorum",
        "vetclinic_api.bft.narwhal",
        "vetclinic_api.bft.hotstuff",
        "vetclinic_api.bft.swim",
    ]:
        assert importlib.import_module(module)


@pytest.mark.bft
@pytest.mark.contract
def test_enum_contract():
    assert {item.name for item in ProtocolName} >= {
        "NARWHAL",
        "HOTSTUFF",
        "SWIM",
        "CHECKPOINTING",
        "RECOVERY",
    }
    assert {item.name for item in OperationStatus} >= {
        "RECEIVED",
        "BATCHED",
        "AVAILABLE",
        "PROPOSED",
        "VOTED",
        "QC_FORMED",
        "COMMITTED",
        "EXECUTED",
        "REJECTED",
        "FAILED",
    }
    assert {item.name for item in NodeStatus} >= {
        "ALIVE",
        "SUSPECT",
        "DEAD",
        "RECOVERING",
    }
    assert {item.name for item in FaultType} >= {
        "CRASH",
        "DELAY",
        "DROP",
        "DUPLICATE",
        "REPLAY",
        "EQUIVOCATION",
        "NETWORK_PARTITION",
        "LEADER_FAILURE",
        "STATE_CORRUPTION",
    }
    assert {item.name for item in MessageKind} >= {
        "CLIENT_OPERATION",
        "BATCH",
        "BATCH_ACK",
        "PROPOSAL",
        "VOTE",
        "QUORUM_CERTIFICATE",
        "COMMIT",
        "SWIM_PING",
        "SWIM_ACK",
        "SWIM_GOSSIP",
        "CHECKPOINT",
        "STATE_TRANSFER",
    }


@pytest.mark.bft
@pytest.mark.contract
def test_quorum_contract():
    expected = {1: (0, 1), 4: (1, 3), 6: (1, 3), 7: (2, 5)}
    for n, (f, quorum) in expected.items():
        assert fault_tolerance(n) == f
        assert quorum_size(n) == quorum
        description = describe_quorum(n)
        assert description["fault_tolerance"] == f
        assert description["quorum"] == quorum
    with pytest.raises(ValueError):
        fault_tolerance(0)
    with pytest.raises(ValueError):
        has_quorum(-1, 4)
    assert has_quorum(2, 4) is False
    assert has_quorum(3, 4) is True


@pytest.mark.bft
@pytest.mark.contract
def test_event_log_contract():
    log = EventLog()
    first = ProtocolEvent(
        event_id="evt-1",
        protocol=ProtocolName.NARWHAL,
        operation_id="op-1",
        status=OperationStatus.BATCHED,
        message="first",
    )
    second = ProtocolEvent(
        event_id="evt-2",
        protocol=ProtocolName.HOTSTUFF,
        operation_id="op-2",
        status=OperationStatus.PROPOSED,
        message="second",
    )
    log.append(first)
    log.append(second)
    assert log.list() == [first, second]
    assert log.by_operation("op-1") == [first]
    log.clear()
    assert log.list() == []


@pytest.mark.bft
@pytest.mark.contract
def test_architecture_router_contract(bft_client):
    assert bft_client.get("/bft/architecture").status_code == 200
    protocols = bft_client.get("/bft/protocols")
    assert protocols.status_code == 200
    names = {item["name"] for item in protocols.json()["protocols"]}
    assert {"Narwhal", "HotStuff", "SWIM"} <= names
    quorum = bft_client.get("/bft/quorum")
    assert quorum.status_code == 200
    payload = quorum.json()
    assert {"total_nodes", "fault_tolerance", "quorum_size"} <= set(payload)
    events = bft_client.get("/bft/events")
    assert events.status_code == 200
    assert isinstance(events.json()["events"], list)
