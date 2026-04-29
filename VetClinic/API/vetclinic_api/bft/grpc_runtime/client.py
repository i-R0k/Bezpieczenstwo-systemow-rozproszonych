from __future__ import annotations

import time
import uuid

import grpc

from vetclinic_api.bft.grpc_runtime.compiler import (
    compile_proto_to_tmp,
    load_generated_modules,
)
from vetclinic_api.bft.grpc_runtime.models import GrpcPingDemoResult


def send_swim_ping(
    host: str,
    port: int,
    source_node_id: int,
    target_node_id: int,
    nonce: str | None = None,
    timeout: float = 3.0,
) -> GrpcPingDemoResult:
    generated_dir = compile_proto_to_tmp()
    pb2, pb2_grpc = load_generated_modules(generated_dir)

    ping_nonce = nonce or str(uuid.uuid4())
    request = pb2.SwimPingMessage(
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        nonce=ping_nonce,
        timestamp_unix_ms=int(time.time() * 1000),
    )

    with grpc.insecure_channel(f"{host}:{port}") as channel:
        stub = pb2_grpc.BftNodeServiceStub(channel)
        response = stub.SendSwimPing(request, timeout=timeout)

    return GrpcPingDemoResult(
        accepted=response.accepted,
        source_node_id=response.source_node_id,
        target_node_id=response.target_node_id,
        nonce=response.nonce,
        status=response.status,
        reason=response.reason or None,
    )
