from __future__ import annotations

from pydantic import BaseModel


class GrpcRuntimeStatus(BaseModel):
    proto_path: str
    generated: bool
    service: str
    methods: list[str]
    implementation_level: str
    runtime_demo_available: bool
    note: str


class GrpcPingDemoResult(BaseModel):
    accepted: bool
    source_node_id: int
    target_node_id: int
    nonce: str
    status: str
    reason: str | None = None
