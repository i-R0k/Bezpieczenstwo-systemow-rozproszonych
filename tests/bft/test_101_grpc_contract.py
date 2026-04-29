from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_grpc_proto_contract_exists_and_declares_service() -> None:
    proto = ROOT / "proto" / "bft.proto"
    assert proto.exists()
    text = proto.read_text(encoding="utf-8")
    assert 'syntax = "proto3";' in text
    assert "service BftNodeService" in text
    for rpc_name in (
        "SendBatch",
        "SendProposal",
        "SendVote",
        "SendSwimPing",
        "SendStateTransferRequest",
    ):
        assert f"rpc {rpc_name}" in text


def test_grpc_documentation_exists() -> None:
    assert (ROOT / "docs" / "GRPC.md").exists()
    assert (ROOT / "proto" / "README.md").exists()


def test_grpc_contract_endpoint(bft_client) -> None:
    response = bft_client.get("/bft/grpc/contract")
    assert response.status_code == 200
    payload = response.json()
    assert payload["proto_path"] == "proto/bft.proto"
    assert payload["service"] == "BftNodeService"
    assert payload["implementation_level"] == "contract-only"
    assert "SendBatch" in payload["methods"]
    assert "FastAPI/in-memory testbed remains primary execution path" in payload["note"]
