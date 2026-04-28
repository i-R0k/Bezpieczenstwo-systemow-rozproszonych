from __future__ import annotations

import threading
from typing import Any


class EquivocationDetector:
    def __init__(self) -> None:
        self._proposals: dict[tuple[int, int], dict[str, list[dict[str, Any]]]] = {}
        self._conflicts: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def record_proposal(
        self,
        view: int,
        proposer_node_id: int,
        target_node_id: int | None,
        proposal_id: str,
        block_id: str,
    ) -> bool:
        with self._lock:
            key = (view, proposer_node_id)
            by_block = self._proposals.setdefault(key, {})
            existing_blocks = set(by_block)
            record = {
                "view": view,
                "proposer_node_id": proposer_node_id,
                "target_node_id": target_node_id,
                "proposal_id": proposal_id,
                "block_id": block_id,
            }
            by_block.setdefault(block_id, []).append(record)
            if existing_blocks and block_id not in existing_blocks:
                conflict = {
                    "view": view,
                    "proposer_node_id": proposer_node_id,
                    "existing_block_ids": sorted(existing_blocks),
                    "conflicting_block_id": block_id,
                    "proposal_id": proposal_id,
                    "target_node_id": target_node_id,
                }
                self._conflicts.append(conflict)
                return True
            return False

    def list_conflicts(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._conflicts)

    def clear(self) -> None:
        with self._lock:
            self._proposals.clear()
            self._conflicts.clear()


EQUIVOCATION_DETECTOR = EquivocationDetector()
