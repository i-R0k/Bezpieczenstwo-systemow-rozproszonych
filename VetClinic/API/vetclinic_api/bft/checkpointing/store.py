from __future__ import annotations

import threading

from vetclinic_api.bft.checkpointing.models import (
    CheckpointCertificate,
    CheckpointStatus,
    StateSnapshot,
)


class InMemoryCheckpointStore:
    def __init__(self) -> None:
        self._snapshots: dict[str, StateSnapshot] = {}
        self._certificates: dict[str, CheckpointCertificate] = {}
        self._latest_certificate_id: str | None = None
        self._lock = threading.Lock()

    def add_snapshot(self, snapshot: StateSnapshot) -> StateSnapshot:
        with self._lock:
            self._snapshots[snapshot.snapshot_id] = snapshot
            return snapshot

    def get_snapshot(self, snapshot_id: str) -> StateSnapshot:
        with self._lock:
            try:
                return self._snapshots[snapshot_id]
            except KeyError as exc:
                raise KeyError(f"Snapshot not found: {snapshot_id}") from exc

    def list_snapshots(self, limit: int = 100) -> list[StateSnapshot]:
        if limit < 0:
            raise ValueError("limit must be greater than or equal to 0")
        with self._lock:
            snapshots = list(self._snapshots.values())
            return [] if limit == 0 else snapshots[-limit:]

    def add_certificate(
        self,
        certificate: CheckpointCertificate,
    ) -> CheckpointCertificate:
        with self._lock:
            self._certificates[certificate.checkpoint_id] = certificate
            self._latest_certificate_id = certificate.checkpoint_id
            return certificate

    def get_certificate(self, checkpoint_id: str) -> CheckpointCertificate:
        with self._lock:
            try:
                return self._certificates[checkpoint_id]
            except KeyError as exc:
                raise KeyError(f"Checkpoint certificate not found: {checkpoint_id}") from exc

    def latest_certificate(self) -> CheckpointCertificate | None:
        with self._lock:
            if not self._latest_certificate_id:
                return None
            return self._certificates[self._latest_certificate_id]

    def list_certificates(self, limit: int = 100) -> list[CheckpointCertificate]:
        if limit < 0:
            raise ValueError("limit must be greater than or equal to 0")
        with self._lock:
            certificates = list(self._certificates.values())
            return [] if limit == 0 else certificates[-limit:]

    def status(self) -> CheckpointStatus:
        return CheckpointStatus(
            snapshots=self.list_snapshots(),
            certificates=self.list_certificates(),
            latest_certificate=self.latest_certificate(),
        )

    def clear(self) -> None:
        with self._lock:
            self._snapshots.clear()
            self._certificates.clear()
            self._latest_certificate_id = None


CHECKPOINT_STORE = InMemoryCheckpointStore()
