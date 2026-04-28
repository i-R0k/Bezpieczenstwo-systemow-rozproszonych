from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class StateTransferRequest(BaseModel):
    request_id: str
    node_id: int
    checkpoint_id: str
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str = "stale_or_crashed_node"


class StateTransferResponse(BaseModel):
    request_id: str
    checkpoint_id: str
    snapshot_id: str
    state_hash: str
    height: int
    state: dict[str, Any]
    committed_after_checkpoint: list[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RecoveryResult(BaseModel):
    node_id: int
    checkpoint_id: str
    snapshot_id: str
    applied_state_hash: str
    replayed_operation_ids: list[str]
    status: str
    recovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RecoveryStatus(BaseModel):
    transfers: list[StateTransferRequest]
    recovered_nodes: list[RecoveryResult]
