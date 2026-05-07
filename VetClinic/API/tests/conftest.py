import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

API_PATH = Path(__file__).resolve().parent.parent
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

import vetclinic_api.blockchain.deps as deps
from vetclinic_api.admin.network_state import NetworkSimState, update_state
import vetclinic_api.cluster.config as cluster_config
import vetclinic_api.routers.bft as bft_router
import vetclinic_api.routers.blockchain as blockchain_router
import vetclinic_api.routers.rpc as rpc_router
from vetclinic_api.crypto.ed25519 import generate_keypair
from vetclinic_api.main import app


@pytest.fixture(autouse=True)
def _leader_keys_env(monkeypatch):
    priv_b64, pub_b64 = generate_keypair()
    monkeypatch.setenv("LEADER_ID", "1")
    monkeypatch.setenv("NODE_ID", "1")
    monkeypatch.delenv("PEERS", raising=False)
    monkeypatch.delenv("LEADER_URL", raising=False)
    monkeypatch.setenv("LEADER_PRIV_KEY", priv_b64)
    monkeypatch.setenv("LEADER_PUB_KEY", pub_b64)
    monkeypatch.setenv("NODE_1_PUB_KEY", pub_b64)


@pytest.fixture(autouse=True)
def _reset_cluster_runtime_config():
    """
    Tests in the root BFT suite mutate the imported CONFIG object for a
    six-node cluster. API endpoint tests expect a standalone leader unless
    they explicitly override it.
    """
    original = cluster_config.NodeConfig(
        node_id=cluster_config.CONFIG.node_id,
        leader_id=cluster_config.CONFIG.leader_id,
        peers=list(cluster_config.CONFIG.peers),
        leader_url=cluster_config.CONFIG.leader_url,
    )

    config_refs = {
        id(cfg): cfg
        for cfg in (
            cluster_config.CONFIG,
            bft_router.CONFIG,
            blockchain_router.CONFIG,
            rpc_router.CONFIG,
        )
    }.values()
    network_router = sys.modules.get("vetclinic_api.admin.network_router")
    if network_router is not None:
        config_refs = list(config_refs) + [network_router.CONFIG]
    for cfg in config_refs:
        cfg.node_id = 1
        cfg.leader_id = 1
        cfg.peers = []
        cfg.leader_url = "http://127.0.0.1:8000"

    yield

    cluster_config.CONFIG.node_id = original.node_id
    cluster_config.CONFIG.leader_id = original.leader_id
    cluster_config.CONFIG.peers = original.peers
    cluster_config.CONFIG.leader_url = original.leader_url


def _reset_network_sim_state() -> None:
    defaults = NetworkSimState()
    payload = {
        key: value
        for key, value in defaults.__dict__.items()
        if not key.startswith("_")
    }
    payload["drop_rpc_probability"] = defaults.drop_rpc_probability
    update_state(**payload)


@pytest.fixture(autouse=True)
def _clean_network_sim_state():
    _reset_network_sim_state()
    yield
    _reset_network_sim_state()


@pytest.fixture(autouse=True)
def _clean_dependency_overrides():
    """
    Ensure dependency overrides from one test do not leak into another.
    """
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _fresh_storage():
    """
    Reset storage reference before each test so DB state does not leak.
    """
    deps._storage = None
    yield
