from __future__ import annotations

import threading

from vetclinic_api.bft.recovery.models import RecoveryResult, RecoveryStatus, StateTransferRequest


class InMemoryRecoveryStore:
    def __init__(self) -> None:
        self._transfers: list[StateTransferRequest] = []
        self._recovered: dict[int, RecoveryResult] = {}
        self._lock = threading.Lock()

    def add_transfer(self, request: StateTransferRequest) -> StateTransferRequest:
        with self._lock:
            self._transfers.append(request)
            return request

    def add_recovery(self, result: RecoveryResult) -> RecoveryResult:
        with self._lock:
            self._recovered[result.node_id] = result
            return result

    def status(self) -> RecoveryStatus:
        with self._lock:
            return RecoveryStatus(
                transfers=list(self._transfers),
                recovered_nodes=list(self._recovered.values()),
            )

    def clear(self) -> None:
        with self._lock:
            self._transfers.clear()
            self._recovered.clear()


RECOVERY_STORE = InMemoryRecoveryStore()
