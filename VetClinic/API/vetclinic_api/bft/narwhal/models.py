from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class NarwhalBatch(BaseModel):
    batch_id: str
    author_node_id: int
    round: int
    operation_ids: list[str]
    parent_batch_ids: list[str]
    payload_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BatchAck(BaseModel):
    batch_id: str
    node_id: int
    accepted: bool
    reason: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BatchCertificate(BaseModel):
    batch_id: str
    ack_node_ids: list[int]
    quorum_size: int
    total_nodes: int
    certified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    available: bool


class DagVertex(BaseModel):
    batch: NarwhalBatch
    certificate: BatchCertificate | None = None
    ack_node_ids: list[int] = Field(default_factory=list)
    children: list[str] = Field(default_factory=list)


class NarwhalDagView(BaseModel):
    vertices: list[DagVertex]
    tips: list[str]
    total_batches: int


class NarwhalBatchRequest(BaseModel):
    operation_ids: list[str] | None = None
    max_operations: int = 10


class NarwhalBatchResponse(BaseModel):
    batch: NarwhalBatch
    certificate: BatchCertificate | None
    operations_marked: list[str]
