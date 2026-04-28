from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from vetclinic_api.bft.common.types import NodeStatus


class SwimMember(BaseModel):
    node_id: int
    address: str
    status: NodeStatus
    incarnation: int = 0
    last_seen: datetime | None = None
    last_status_change: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    suspicion_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class SwimPing(BaseModel):
    source_node_id: int
    target_node_id: int
    nonce: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SwimAck(BaseModel):
    source_node_id: int
    target_node_id: int
    nonce: str
    accepted: bool
    status: NodeStatus
    incarnation: int
    reason: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SwimPingReq(BaseModel):
    source_node_id: int
    intermediary_node_id: int
    target_node_id: int
    nonce: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SwimGossipUpdate(BaseModel):
    node_id: int
    status: NodeStatus
    incarnation: int
    observed_by: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    reason: str | None = None


class SwimGossipEnvelope(BaseModel):
    source_node_id: int
    updates: list[SwimGossipUpdate]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SwimStatus(BaseModel):
    self_node_id: int
    members: list[SwimMember]
    alive: int
    suspect: int
    dead: int
    recovering: int


class SwimProbeResult(BaseModel):
    ping: SwimPing
    ack: SwimAck | None
    status_before: NodeStatus | None
    status_after: NodeStatus
    indirect_probes: list[SwimAck] = Field(default_factory=list)
