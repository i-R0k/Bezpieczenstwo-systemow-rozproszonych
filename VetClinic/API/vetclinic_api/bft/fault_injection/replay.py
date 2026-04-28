from __future__ import annotations

import threading


class ReplayGuard:
    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._lock = threading.Lock()

    def seen(self, message_id: str) -> bool:
        with self._lock:
            return message_id in self._seen

    def mark_seen(self, message_id: str) -> None:
        with self._lock:
            self._seen.add(message_id)

    def check_and_mark(self, message_id: str) -> bool:
        with self._lock:
            if message_id in self._seen:
                return True
            self._seen.add(message_id)
            return False

    def clear(self) -> None:
        with self._lock:
            self._seen.clear()


REPLAY_GUARD = ReplayGuard()
