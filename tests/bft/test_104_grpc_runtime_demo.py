from __future__ import annotations

from vetclinic_api.bft.common.events import EVENT_LOG
from vetclinic_api.bft.grpc_runtime.client import send_swim_ping
from vetclinic_api.bft.grpc_runtime.compiler import (
    compile_proto_to_tmp,
    load_generated_modules,
)
from vetclinic_api.bft.grpc_runtime.server import (
    start_grpc_demo_server,
    stop_grpc_demo_server,
)


def test_compile_proto_to_tmp_generates_python_modules() -> None:
    generated_dir = compile_proto_to_tmp()

    assert (generated_dir / "bft_pb2.py").exists()
    assert (generated_dir / "bft_pb2_grpc.py").exists()

    bft_pb2, bft_pb2_grpc = load_generated_modules(generated_dir)
    assert hasattr(bft_pb2, "SwimPingMessage")
    assert hasattr(bft_pb2_grpc, "BftNodeServiceStub")


def test_grpc_swim_ping_runtime_records_event(event_log) -> None:
    server, bound_port = start_grpc_demo_server("127.0.0.1", 0, EVENT_LOG)
    try:
        result = send_swim_ping(
            "127.0.0.1",
            bound_port,
            source_node_id=1,
            target_node_id=2,
            nonce="runtime-test-nonce",
        )
    finally:
        stop_grpc_demo_server(server)

    assert result.accepted is True
    assert result.status == "ALIVE"
    assert result.source_node_id == 2
    assert result.target_node_id == 1
    assert any(event.message == "grpc_swim_ping_received" for event in event_log.list())


def test_grpc_runtime_status_endpoint(bft_client) -> None:
    response = bft_client.get("/bft/grpc/runtime/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "BftNodeService"
    assert payload["implementation_level"] == "demo-runtime"
    assert payload["runtime_demo_available"] is True
    assert "SendSwimPing" in payload["methods"]


def test_grpc_runtime_ping_demo_endpoint(bft_client) -> None:
    response = bft_client.post(
        "/bft/grpc/runtime/ping-demo",
        params={"source_node_id": 1, "target_node_id": 2},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] is True
    assert payload["status"] == "ALIVE"
    assert payload["source_node_id"] == 2
    assert payload["target_node_id"] == 1
