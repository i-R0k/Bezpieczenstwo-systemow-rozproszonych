from __future__ import annotations

import sys
from pathlib import Path

API_PATH = Path(__file__).resolve().parents[1] / "VetClinic" / "API"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from vetclinic_api.bft.common.events import EventLog  # noqa: E402
from vetclinic_api.bft.common.types import NodeStatus  # noqa: E402
from vetclinic_api.bft.swim.models import SwimGossipUpdate  # noqa: E402
from vetclinic_api.bft.swim.service import SwimService  # noqa: E402
from vetclinic_api.bft.swim.store import InMemorySwimStore  # noqa: E402


def _service() -> tuple[SwimService, InMemorySwimStore, EventLog]:
    store = InMemorySwimStore()
    log = EventLog()
    service = SwimService(store, log)
    service.bootstrap(1, "http://node1:8000", ["http://node2:8000", "http://node3:8000"])
    return service, store, log


def test_ping_success_returns_ack_and_alive() -> None:
    service, store, _ = _service()
    store.mark_suspect(2)

    result = service.ping(1, 2, simulate_success=True)

    assert result.ack is not None
    assert result.ack.accepted is True
    assert result.status_after == NodeStatus.ALIVE
    assert store.get_member(2).status == NodeStatus.ALIVE


def test_ping_fail_marks_suspect() -> None:
    service, store, _ = _service()

    result = service.ping(1, 2, simulate_success=False)

    assert result.ack is None
    assert result.status_after == NodeStatus.SUSPECT
    assert store.get_member(2).suspicion_count == 1


def test_two_ping_failures_mark_dead() -> None:
    service, store, _ = _service()

    service.ping(1, 2, simulate_success=False)
    result = service.ping(1, 2, simulate_success=False)

    assert result.status_after == NodeStatus.DEAD
    assert store.get_member(2).status == NodeStatus.DEAD


def test_ping_req_success_returns_accepted() -> None:
    service, _, _ = _service()

    ack = service.ping_req(1, 3, 2, simulate_success=True)

    assert ack.accepted is True
    assert ack.status == NodeStatus.ALIVE


def test_probe_demo_direct_success_ends_alive() -> None:
    service, _, _ = _service()

    result = service.probe_demo(2, self_node_id=1, total_nodes=3)

    assert result.status_after == NodeStatus.ALIVE
    assert result.ack is not None
    assert result.indirect_probes == []


def test_probe_demo_direct_fail_indirect_success_ends_alive() -> None:
    service, _, _ = _service()

    result = service.probe_demo(
        2,
        self_node_id=1,
        total_nodes=3,
        fail_direct=True,
        fail_indirect=False,
    )

    assert result.status_after == NodeStatus.ALIVE
    assert result.ack is not None
    assert len(result.indirect_probes) == 1


def test_probe_demo_direct_fail_indirect_fail_ends_suspect_or_dead() -> None:
    service, _, _ = _service()

    result = service.probe_demo(
        2,
        self_node_id=1,
        total_nodes=3,
        fail_direct=True,
        fail_indirect=True,
    )

    assert result.status_after in {NodeStatus.SUSPECT, NodeStatus.DEAD}
    assert result.ack is None


def test_gossip_applies_update() -> None:
    service, store, _ = _service()

    service.gossip(
        1,
        [
            SwimGossipUpdate(
                node_id=2,
                status=NodeStatus.DEAD,
                incarnation=1,
                observed_by=1,
            )
        ],
    )

    assert store.get_member(2).status == NodeStatus.DEAD


def test_event_log_contains_swim_events() -> None:
    service, _, log = _service()

    service.ping(1, 2, simulate_success=True)
    service.ping(1, 2, simulate_success=False)
    service.gossip(
        1,
        [
            SwimGossipUpdate(
                node_id=3,
                status=NodeStatus.SUSPECT,
                incarnation=1,
                observed_by=1,
            )
        ],
    )

    messages = [event.message for event in log.list(limit=100)]
    assert "swim_bootstrap" in messages
    assert "swim_ping_ack" in messages
    assert "swim_ping_missed" in messages
    assert "swim_gossip_applied" in messages
