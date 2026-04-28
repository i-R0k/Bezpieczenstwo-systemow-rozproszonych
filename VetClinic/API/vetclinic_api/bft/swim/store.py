from __future__ import annotations

import re
import threading
from datetime import datetime, timezone
from urllib.parse import urlparse

from vetclinic_api.bft.common.types import NodeStatus
from vetclinic_api.bft.swim.models import (
    SwimGossipUpdate,
    SwimMember,
    SwimStatus,
)

STATUS_STRENGTH = {
    NodeStatus.ALIVE: 0,
    NodeStatus.RECOVERING: 1,
    NodeStatus.SUSPECT: 2,
    NodeStatus.DEAD: 3,
}


class InMemorySwimStore:
    def __init__(self) -> None:
        self._members: dict[int, SwimMember] = {}
        self._lock = threading.Lock()

    def upsert_member(
        self,
        node_id: int,
        address: str,
        status: NodeStatus = NodeStatus.ALIVE,
        incarnation: int = 0,
        metadata: dict | None = None,
    ) -> SwimMember:
        now = datetime.now(timezone.utc)
        with self._lock:
            current = self._members.get(node_id)
            member = SwimMember(
                node_id=node_id,
                address=address,
                status=status,
                incarnation=incarnation,
                last_seen=now if status == NodeStatus.ALIVE else current.last_seen if current else None,
                last_status_change=now,
                suspicion_count=current.suspicion_count if current else 0,
                metadata=metadata or (current.metadata if current else {}),
            )
            self._members[node_id] = member
            return member

    def get_member(self, node_id: int) -> SwimMember:
        with self._lock:
            try:
                return self._members[node_id]
            except KeyError as exc:
                raise KeyError(f"SWIM member not found: {node_id}") from exc

    def list_members(self) -> list[SwimMember]:
        with self._lock:
            return list(self._members.values())

    def mark_alive(
        self,
        node_id: int,
        incarnation: int | None = None,
        reason: str = "ack",
    ) -> SwimMember:
        del reason
        with self._lock:
            member = self._require_member(node_id)
            next_incarnation = (
                incarnation
                if incarnation is not None
                else member.incarnation + 1
                if member.status == NodeStatus.DEAD
                else member.incarnation
            )
            updated = member.model_copy(
                update={
                    "status": NodeStatus.ALIVE,
                    "incarnation": max(next_incarnation, member.incarnation),
                    "last_seen": datetime.now(timezone.utc),
                    "last_status_change": datetime.now(timezone.utc),
                    "suspicion_count": 0,
                }
            )
            self._members[node_id] = updated
            return updated

    def mark_suspect(
        self,
        node_id: int,
        reason: str = "missed_ack",
    ) -> SwimMember:
        del reason
        with self._lock:
            member = self._require_member(node_id)
            updated = member.model_copy(
                update={
                    "status": NodeStatus.SUSPECT,
                    "last_status_change": datetime.now(timezone.utc),
                    "suspicion_count": member.suspicion_count + 1,
                }
            )
            self._members[node_id] = updated
            return updated

    def mark_dead(
        self,
        node_id: int,
        reason: str = "suspicion_threshold",
    ) -> SwimMember:
        del reason
        with self._lock:
            member = self._require_member(node_id)
            updated = member.model_copy(
                update={
                    "status": NodeStatus.DEAD,
                    "last_status_change": datetime.now(timezone.utc),
                }
            )
            self._members[node_id] = updated
            return updated

    def mark_recovering(
        self,
        node_id: int,
        reason: str = "state_sync_required",
    ) -> SwimMember:
        del reason
        with self._lock:
            member = self._require_member(node_id)
            updated = member.model_copy(
                update={
                    "status": NodeStatus.RECOVERING,
                    "last_status_change": datetime.now(timezone.utc),
                }
            )
            self._members[node_id] = updated
            return updated

    def apply_gossip(self, update: SwimGossipUpdate) -> SwimMember:
        with self._lock:
            current = self._members.get(update.node_id)
            if current is None:
                member = SwimMember(
                    node_id=update.node_id,
                    address=f"node-{update.node_id}",
                    status=update.status,
                    incarnation=update.incarnation,
                    last_seen=update.timestamp if update.status == NodeStatus.ALIVE else None,
                    last_status_change=update.timestamp,
                )
                self._members[update.node_id] = member
                return member

            should_apply = (
                update.incarnation > current.incarnation
                or (
                    update.incarnation == current.incarnation
                    and STATUS_STRENGTH[update.status] > STATUS_STRENGTH[current.status]
                )
            )
            if not should_apply:
                return current

            updated = current.model_copy(
                update={
                    "status": update.status,
                    "incarnation": update.incarnation,
                    "last_seen": update.timestamp
                    if update.status == NodeStatus.ALIVE
                    else current.last_seen,
                    "last_status_change": update.timestamp,
                    "suspicion_count": 0
                    if update.status == NodeStatus.ALIVE
                    else current.suspicion_count,
                }
            )
            self._members[update.node_id] = updated
            return updated

    def status(self, self_node_id: int) -> SwimStatus:
        with self._lock:
            members = list(self._members.values())
        return SwimStatus(
            self_node_id=self_node_id,
            members=members,
            alive=sum(1 for member in members if member.status == NodeStatus.ALIVE),
            suspect=sum(1 for member in members if member.status == NodeStatus.SUSPECT),
            dead=sum(1 for member in members if member.status == NodeStatus.DEAD),
            recovering=sum(
                1 for member in members if member.status == NodeStatus.RECOVERING
            ),
        )

    def bootstrap_from_config(
        self,
        self_node_id: int,
        self_address: str,
        peers: list[str],
    ) -> list[SwimMember]:
        self.upsert_member(self_node_id, self_address, NodeStatus.ALIVE)
        next_fallback_id = 1
        for peer in peers:
            node_id = self._node_id_from_peer(peer)
            if node_id is None:
                while next_fallback_id == self_node_id or next_fallback_id in self._members:
                    next_fallback_id += 1
                node_id = next_fallback_id
            if node_id == self_node_id:
                continue
            self.upsert_member(node_id, peer, NodeStatus.ALIVE)
        return self.list_members()

    def clear(self) -> None:
        with self._lock:
            self._members.clear()

    def _require_member(self, node_id: int) -> SwimMember:
        try:
            return self._members[node_id]
        except KeyError as exc:
            raise KeyError(f"SWIM member not found: {node_id}") from exc

    @staticmethod
    def _node_id_from_peer(peer: str) -> int | None:
        try:
            parsed = urlparse(peer)
        except Exception:
            parsed = None
        host = parsed.hostname if parsed else peer
        if not host:
            return None
        match = re.search(r"node(\d+)", host.lower())
        if match:
            return int(match.group(1))
        return None


SWIM_STORE = InMemorySwimStore()
