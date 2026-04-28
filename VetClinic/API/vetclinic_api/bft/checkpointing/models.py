from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class StateSnapshot(BaseModel):
    snapshot_id: str
    node_id: int
    height: int
    operation_ids: list[str]
    state: dict[str, Any]
    state_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CheckpointCertificate(BaseModel):
    checkpoint_id: str
    snapshot_id: str
    state_hash: str
    height: int
    signer_node_ids: list[int]
    quorum_size: int
    total_nodes: int
    certified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid: bool = True


class CheckpointStatus(BaseModel):
    snapshots: list[StateSnapshot]
    certificates: list[CheckpointCertificate]
    latest_certificate: CheckpointCertificate | None = None


class CheckpointCreateRequest(BaseModel):
    node_id: int | None = None


class CheckpointCertifyRequest(BaseModel):
    signer_node_ids: list[int] | None = None
