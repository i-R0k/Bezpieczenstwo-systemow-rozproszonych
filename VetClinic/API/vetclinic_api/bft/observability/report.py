from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class BftDemoStep(BaseModel):
    step_id: str
    name: str
    status: str
    started_at: datetime
    finished_at: datetime
    details: dict[str, Any] = Field(default_factory=dict)


class BftDemoReport(BaseModel):
    report_id: str
    status: str
    started_at: datetime
    finished_at: datetime
    steps: list[BftDemoStep]
    operation_id: str | None = None
    final_operation_status: str | None = None
    checkpoint_id: str | None = None
    recovered_node_id: int | None = None
    metrics_snapshot: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


def build_step(name: str, status: str, started_at: datetime, details: dict[str, Any]) -> BftDemoStep:
    return BftDemoStep(
        step_id=str(uuid.uuid4()),
        name=name,
        status=status,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        details=details,
    )
