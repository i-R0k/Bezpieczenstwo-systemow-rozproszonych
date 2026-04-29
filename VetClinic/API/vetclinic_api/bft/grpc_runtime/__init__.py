"""Local gRPC runtime demo for BFT node-to-node contracts."""

from vetclinic_api.bft.grpc_runtime.client import send_swim_ping
from vetclinic_api.bft.grpc_runtime.compiler import (
    compile_proto_to_tmp,
    load_generated_modules,
)
from vetclinic_api.bft.grpc_runtime.server import (
    start_grpc_demo_server,
    stop_grpc_demo_server,
)

__all__ = [
    "compile_proto_to_tmp",
    "load_generated_modules",
    "send_swim_ping",
    "start_grpc_demo_server",
    "stop_grpc_demo_server",
]
