from __future__ import annotations

import sys
from pathlib import Path

API_PATH = Path(__file__).resolve().parents[1] / "VetClinic" / "API"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from vetclinic_api.bft.common.types import NodeStatus  # noqa: E402
from vetclinic_api.bft.swim.models import SwimGossipUpdate  # noqa: E402
from vetclinic_api.bft.swim.store import InMemorySwimStore  # noqa: E402


def test_bootstrap_adds_self_and_peers() -> None:
    store = InMemorySwimStore()

    members = store.bootstrap_from_config(
        self_node_id=1,
        self_address="http://node1:8000",
        peers=["http://node2:8000", "http://node3:8000"],
    )

    assert {member.node_id for member in members} == {1, 2, 3}
    assert all(member.status == NodeStatus.ALIVE for member in members)


def test_mark_alive_sets_alive() -> None:
    store = InMemorySwimStore()
    store.upsert_member(2, "http://node2:8000", NodeStatus.SUSPECT)

    member = store.mark_alive(2)

    assert member.status == NodeStatus.ALIVE
    assert member.suspicion_count == 0


def test_mark_suspect_increases_suspicion_count() -> None:
    store = InMemorySwimStore()
    store.upsert_member(2, "http://node2:8000")

    first = store.mark_suspect(2)
    second = store.mark_suspect(2)

    assert first.suspicion_count == 1
    assert second.suspicion_count == 2
    assert second.status == NodeStatus.SUSPECT


def test_apply_gossip_ignores_older_incarnation() -> None:
    store = InMemorySwimStore()
    store.upsert_member(2, "http://node2:8000", NodeStatus.ALIVE, incarnation=3)

    member = store.apply_gossip(
        SwimGossipUpdate(
            node_id=2,
            status=NodeStatus.DEAD,
            incarnation=2,
            observed_by=1,
        )
    )

    assert member.status == NodeStatus.ALIVE
    assert member.incarnation == 3


def test_apply_gossip_uses_newer_incarnation() -> None:
    store = InMemorySwimStore()
    store.upsert_member(2, "http://node2:8000", NodeStatus.ALIVE, incarnation=1)

    member = store.apply_gossip(
        SwimGossipUpdate(
            node_id=2,
            status=NodeStatus.SUSPECT,
            incarnation=2,
            observed_by=1,
        )
    )

    assert member.status == NodeStatus.SUSPECT
    assert member.incarnation == 2


def test_apply_gossip_uses_stronger_status_for_same_incarnation() -> None:
    store = InMemorySwimStore()
    store.upsert_member(2, "http://node2:8000", NodeStatus.RECOVERING, incarnation=1)

    member = store.apply_gossip(
        SwimGossipUpdate(
            node_id=2,
            status=NodeStatus.DEAD,
            incarnation=1,
            observed_by=1,
        )
    )

    assert member.status == NodeStatus.DEAD


def test_mark_alive_for_dead_increases_incarnation() -> None:
    store = InMemorySwimStore()
    store.upsert_member(2, "http://node2:8000", NodeStatus.ALIVE, incarnation=1)
    store.mark_dead(2)

    member = store.mark_alive(2)

    assert member.status == NodeStatus.ALIVE
    assert member.incarnation == 2


def test_clear_removes_members() -> None:
    store = InMemorySwimStore()
    store.upsert_member(1, "http://node1:8000")

    store.clear()

    assert store.list_members() == []
