from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone
from typing import Any

from vetclinic_api.bft.common.quorum import quorum_size
from vetclinic_api.bft.narwhal.models import (
    BatchAck,
    BatchCertificate,
    DagVertex,
    NarwhalBatch,
    NarwhalDagView,
)


def _stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class InMemoryNarwhalStore:
    def __init__(self, total_nodes: int = 1) -> None:
        if total_nodes <= 0:
            raise ValueError("total_nodes must be greater than 0")
        self._total_nodes = total_nodes
        self._vertices: dict[str, DagVertex] = {}
        self._acks: dict[str, dict[int, BatchAck]] = {}
        self._certificates: dict[str, BatchCertificate] = {}
        self._tips: list[str] = []
        self._round = 0
        self._lock = threading.Lock()

    def set_total_nodes(self, total_nodes: int) -> None:
        if total_nodes <= 0:
            raise ValueError("total_nodes must be greater than 0")
        with self._lock:
            self._total_nodes = total_nodes

    def next_round(self) -> int:
        with self._lock:
            return self._round + 1

    def create_batch(
        self,
        author_node_id: int,
        round: int,
        operation_ids: list[str],
        parent_batch_ids: list[str],
    ) -> NarwhalBatch:
        if not operation_ids:
            raise ValueError("operation_ids must not be empty")

        timestamp = datetime.now(timezone.utc)
        payload_hash = _stable_hash(operation_ids)
        batch_id = _stable_hash(
            {
                "author_node_id": author_node_id,
                "round": round,
                "operation_ids": operation_ids,
                "parent_batch_ids": parent_batch_ids,
                "timestamp": timestamp.isoformat(),
            }
        )
        batch = NarwhalBatch(
            batch_id=batch_id,
            author_node_id=author_node_id,
            round=round,
            operation_ids=list(operation_ids),
            parent_batch_ids=list(parent_batch_ids),
            payload_hash=payload_hash,
            created_at=timestamp,
        )
        return self.add_batch(batch)

    def add_batch(self, batch: NarwhalBatch) -> NarwhalBatch:
        if not batch.operation_ids:
            raise ValueError("operation_ids must not be empty")

        with self._lock:
            if batch.batch_id in self._vertices:
                return self._vertices[batch.batch_id].batch

            missing_parents = [
                parent_id
                for parent_id in batch.parent_batch_ids
                if parent_id not in self._vertices
            ]
            if missing_parents:
                raise KeyError(f"Parent batch not found: {missing_parents[0]}")

            vertex = DagVertex(batch=batch)
            self._vertices[batch.batch_id] = vertex
            self._acks[batch.batch_id] = {}
            for parent_id in batch.parent_batch_ids:
                parent = self._vertices[parent_id]
                if batch.batch_id not in parent.children:
                    parent.children.append(batch.batch_id)

            self._tips = [
                tip
                for tip in self._tips
                if tip not in set(batch.parent_batch_ids)
            ]
            self._tips.append(batch.batch_id)
            self._round = max(self._round, batch.round)
            return batch

    def get_batch(self, batch_id: str) -> NarwhalBatch:
        with self._lock:
            try:
                return self._vertices[batch_id].batch
            except KeyError as exc:
                raise KeyError(f"Batch not found: {batch_id}") from exc

    def list_batches(self, limit: int = 100) -> list[NarwhalBatch]:
        if limit < 0:
            raise ValueError("limit must be greater than or equal to 0")
        with self._lock:
            batches = [vertex.batch for vertex in self._vertices.values()]
            if limit == 0:
                return []
            return batches[-limit:]

    def add_ack(self, ack: BatchAck) -> BatchCertificate | None:
        with self._lock:
            if ack.batch_id not in self._vertices:
                raise KeyError(f"Batch not found: {ack.batch_id}")

            batch_acks = self._acks[ack.batch_id]
            if ack.node_id not in batch_acks:
                batch_acks[ack.node_id] = ack

            vertex = self._vertices[ack.batch_id]
            vertex.ack_node_ids = sorted(batch_acks)

            if ack.batch_id in self._certificates:
                return self._certificates[ack.batch_id]

            accepted_nodes = sorted(
                node_id
                for node_id, batch_ack in batch_acks.items()
                if batch_ack.accepted
            )
            required = quorum_size(self._total_nodes)
            if len(accepted_nodes) >= required:
                certificate = BatchCertificate(
                    batch_id=ack.batch_id,
                    ack_node_ids=accepted_nodes,
                    quorum_size=required,
                    total_nodes=self._total_nodes,
                    certified_at=datetime.now(timezone.utc),
                    available=True,
                )
                self._certificates[ack.batch_id] = certificate
                vertex.certificate = certificate
                return certificate

            return None

    def get_certificate(self, batch_id: str) -> BatchCertificate | None:
        with self._lock:
            if batch_id not in self._vertices:
                raise KeyError(f"Batch not found: {batch_id}")
            return self._certificates.get(batch_id)

    def get_dag(self) -> NarwhalDagView:
        with self._lock:
            return NarwhalDagView(
                vertices=[
                    vertex.model_copy(
                        update={
                            "ack_node_ids": list(vertex.ack_node_ids),
                            "children": list(vertex.children),
                        }
                    )
                    for vertex in self._vertices.values()
                ],
                tips=list(self._tips),
                total_batches=len(self._vertices),
            )

    def get_tips(self) -> list[str]:
        with self._lock:
            return list(self._tips)

    def clear(self) -> None:
        with self._lock:
            self._vertices.clear()
            self._acks.clear()
            self._certificates.clear()
            self._tips.clear()
            self._round = 0


NARWHAL_STORE = InMemoryNarwhalStore()
