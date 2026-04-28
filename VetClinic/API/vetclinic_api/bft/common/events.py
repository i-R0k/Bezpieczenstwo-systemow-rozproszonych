from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from vetclinic_api.bft.common.types import OperationStatus, ProtocolName


class ProtocolEvent(BaseModel):
    event_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    node_id: int | None = None
    protocol: ProtocolName
    operation_id: str | None = None
    status: OperationStatus | None = None
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class EventLog:
    """Small in-memory protocol event store for tests and diagnostics."""

    def __init__(self) -> None:
        self._events: list[ProtocolEvent] = []
        self._lock = threading.Lock()

    def append(self, event: ProtocolEvent) -> ProtocolEvent:
        with self._lock:
            self._events.append(event)
        try:
            from vetclinic_api.bft.observability.metrics import BFT_METRICS

            BFT_METRICS.record_event(event)
        except Exception:
            pass
        return event

    def list(self, limit: int = 100) -> list[ProtocolEvent]:
        if limit < 0:
            raise ValueError("limit must be greater than or equal to 0")
        with self._lock:
            if limit == 0:
                return []
            return list(self._events[-limit:])

    def by_operation(self, operation_id: str) -> list[ProtocolEvent]:
        with self._lock:
            return [
                event
                for event in self._events
                if event.operation_id == operation_id
            ]

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


EVENT_LOG = EventLog()
