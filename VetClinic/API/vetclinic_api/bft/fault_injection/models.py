from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from vetclinic_api.bft.common.types import FaultType, MessageKind, ProtocolName


class FaultRule(BaseModel):
    rule_id: str
    fault_type: FaultType
    protocol: ProtocolName | None = None
    source_node_id: int | None = None
    target_node_id: int | None = None
    message_kind: MessageKind | None = None
    enabled: bool = True
    probability: float = Field(default=1.0, ge=0.0, le=1.0)
    delay_ms: int | None = Field(default=None, ge=0)
    partition_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InjectedFault(BaseModel):
    fault_id: str
    rule_id: str
    fault_type: FaultType
    protocol: ProtocolName | None = None
    source_node_id: int | None = None
    target_node_id: int | None = None
    message_kind: MessageKind | None = None
    operation_id: str | None = None
    message_id: str | None = None
    applied: bool
    reason: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class FaultDecision(BaseModel):
    should_drop: bool = False
    should_delay: bool = False
    delay_ms: int = 0
    should_duplicate: bool = False
    should_replay: bool = False
    should_equivocate: bool = False
    blocked_by_partition: bool = False
    leader_failed: bool = False
    injected_faults: list[InjectedFault] = Field(default_factory=list)


class NetworkPartition(BaseModel):
    partition_id: str
    groups: list[list[int]]
    enabled: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FaultInjectionStatus(BaseModel):
    rules: list[FaultRule]
    partitions: list[NetworkPartition]
    injected_faults: list[InjectedFault]
    counters: dict[str, int]


class FaultEvaluationContext(BaseModel):
    protocol: ProtocolName
    message_kind: MessageKind
    source_node_id: int | None = None
    target_node_id: int | None = None
    operation_id: str | None = None
    message_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
