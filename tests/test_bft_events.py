from __future__ import annotations

import sys
from pathlib import Path

import pytest

API_PATH = Path(__file__).resolve().parents[1] / "VetClinic" / "API"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from vetclinic_api.bft.common.events import EventLog, ProtocolEvent  # noqa: E402
from vetclinic_api.bft.common.types import OperationStatus, ProtocolName  # noqa: E402


def _event(event_id: str, operation_id: str | None) -> ProtocolEvent:
    return ProtocolEvent(
        event_id=event_id,
        node_id=1,
        protocol=ProtocolName.HOTSTUFF,
        operation_id=operation_id,
        status=OperationStatus.RECEIVED,
        message=f"event {event_id}",
        details={"source": "test"},
    )


def test_event_log_append_list_by_operation_and_clear() -> None:
    log = EventLog()
    first = _event("evt-1", "op-1")
    second = _event("evt-2", "op-2")
    third = _event("evt-3", "op-1")

    assert log.append(first) == first
    log.append(second)
    log.append(third)

    assert log.list() == [first, second, third]
    assert log.list(limit=2) == [second, third]
    assert log.list(limit=0) == []
    assert log.by_operation("op-1") == [first, third]
    assert log.by_operation("missing") == []

    log.clear()
    assert log.list() == []


def test_event_log_rejects_negative_limit() -> None:
    log = EventLog()
    with pytest.raises(ValueError):
        log.list(limit=-1)
