from __future__ import annotations

import uuid
from concurrent import futures
from typing import Any

import grpc

from vetclinic_api.bft.common.events import EVENT_LOG, EventLog, ProtocolEvent
from vetclinic_api.bft.common.types import MessageKind, ProtocolName
from vetclinic_api.bft.grpc_runtime.compiler import (
    compile_proto_to_tmp,
    load_generated_modules,
)


def _not_implemented_ack(pb2: Any) -> Any:
    return pb2.Ack(
        accepted=False,
        reason="not_implemented_in_demo_runtime",
    )


def _build_servicer(pb2: Any, pb2_grpc: Any, event_log: EventLog):
    class BftNodeGrpcServicer(pb2_grpc.BftNodeServiceServicer):
        def __init__(self, event_log: EventLog) -> None:
            self.event_log = event_log

        def SendBatch(self, request, context):
            return _not_implemented_ack(pb2)

        def SendBatchAck(self, request, context):
            return _not_implemented_ack(pb2)

        def SendProposal(self, request, context):
            return _not_implemented_ack(pb2)

        def SendVote(self, request, context):
            return _not_implemented_ack(pb2)

        def SendSwimPing(self, request, context):
            self.event_log.append(
                ProtocolEvent(
                    event_id=str(uuid.uuid4()),
                    node_id=request.target_node_id,
                    protocol=ProtocolName.SWIM,
                    message="grpc_swim_ping_received",
                    details={
                        "source_node_id": request.source_node_id,
                        "target_node_id": request.target_node_id,
                        "nonce": request.nonce,
                        "message_kind": MessageKind.SWIM_PING.value,
                        "transport": "grpc",
                    },
                )
            )
            return pb2.SwimAckMessage(
                source_node_id=request.target_node_id,
                target_node_id=request.source_node_id,
                nonce=request.nonce,
                accepted=True,
                status="ALIVE",
                incarnation=0,
                reason="grpc_demo_ack",
            )

        def SendSwimGossip(self, request, context):
            return _not_implemented_ack(pb2)

        def SendStateTransferRequest(self, request, context):
            return _not_implemented_ack(pb2)

        def SendStateTransferResponse(self, request, context):
            return _not_implemented_ack(pb2)

    return BftNodeGrpcServicer(event_log)


def start_grpc_demo_server(
    host: str,
    port: int,
    event_log: EventLog = EVENT_LOG,
) -> tuple[grpc.Server, int]:
    generated_dir = compile_proto_to_tmp()
    pb2, pb2_grpc = load_generated_modules(generated_dir)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    pb2_grpc.add_BftNodeServiceServicer_to_server(
        _build_servicer(pb2, pb2_grpc, event_log),
        server,
    )
    bound_port = server.add_insecure_port(f"{host}:{port}")
    if bound_port == 0:
        raise RuntimeError(f"Could not bind gRPC demo server on {host}:{port}")
    server.start()
    return server, bound_port


def stop_grpc_demo_server(server: grpc.Server) -> None:
    server.stop(grace=None).wait(timeout=3)
