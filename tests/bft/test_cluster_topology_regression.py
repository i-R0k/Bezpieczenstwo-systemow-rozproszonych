from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

import vetclinic_api.routers.bft as bft_module
from vetclinic_api.cluster.config import NodeConfig
from vetclinic_api.routers.bft import router as bft_router


def _client_with_config(config: NodeConfig, monkeypatch) -> TestClient:
    monkeypatch.setattr(bft_module, "CONFIG", config)
    app = FastAPI()
    app.include_router(bft_router)
    return TestClient(app)


def test_bft_topology_reports_six_nodes_when_five_peers_are_configured(monkeypatch) -> None:
    client = _client_with_config(
        NodeConfig(
            node_id=1,
            leader_id=1,
            peers=[
                "http://node2:8000",
                "http://node3:8000",
                "http://node4:8000",
                "http://node5:8000",
                "http://node6:8000",
            ],
            leader_url="http://node1:8000",
        ),
        monkeypatch,
    )

    topology = client.get("/bft/cluster/topology").json()
    status = client.get("/bft/status").json()

    assert topology["configured_total_nodes"] == 6
    assert topology["warning"] is None
    assert status["cluster_topology"]["configured_total_nodes"] == 6
    assert status["quorum"]["summary"]["nodes"] == 6


def test_bft_topology_reports_standalone_warning_without_peers(monkeypatch) -> None:
    client = _client_with_config(
        NodeConfig(node_id=1, leader_id=1, peers=[], leader_url="http://127.0.0.1:8000"),
        monkeypatch,
    )

    topology = client.get("/bft/cluster/topology").json()
    status = client.get("/bft/status").json()

    assert topology["configured_total_nodes"] == 1
    assert "standalone/no peers" in topology["warning"]
    assert status["cluster_topology"]["configured_total_nodes"] == 1
    assert "standalone/no peers" in status["cluster_topology"]["warning"]
