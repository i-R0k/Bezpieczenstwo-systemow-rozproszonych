from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


API_PATH = Path(__file__).resolve().parents[2] / "VetClinic" / "API"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from vetclinic_api.bft.common.events import EVENT_LOG  # noqa: E402
from vetclinic_api.bft.common.operations import OPERATION_STORE  # noqa: E402
from vetclinic_api.bft.crypto.registry import NODE_KEY_REGISTRY  # noqa: E402
from vetclinic_api.bft.fault_injection.equivocation import EQUIVOCATION_DETECTOR  # noqa: E402
from vetclinic_api.bft.fault_injection.replay import REPLAY_GUARD  # noqa: E402
from vetclinic_api.bft.fault_injection.store import FAULT_STORE  # noqa: E402
from vetclinic_api.bft.checkpointing.store import CHECKPOINT_STORE  # noqa: E402
from vetclinic_api.bft.hotstuff.store import HOTSTUFF_STORE  # noqa: E402
from vetclinic_api.bft.narwhal.store import NARWHAL_STORE  # noqa: E402
from vetclinic_api.bft.observability.metrics import BFT_METRICS  # noqa: E402
from vetclinic_api.bft.recovery.store import RECOVERY_STORE  # noqa: E402
from vetclinic_api.bft.swim.store import SWIM_STORE  # noqa: E402
import vetclinic_api.routers.bft as bft_module  # noqa: E402
from vetclinic_api.routers.bft import router as bft_router  # noqa: E402


def _configure_bft_router_for_security_tests() -> None:
    bft_module.CONFIG.node_id = 1
    bft_module.CONFIG.leader_id = 1
    bft_module.CONFIG.peers = [
        "http://node2:8000",
        "http://node3:8000",
        "http://node4:8000",
        "http://node5:8000",
        "http://node6:8000",
    ]
    bft_module.CONFIG.leader_url = "http://node1:8000"


def _clear_bft_state() -> None:
    OPERATION_STORE.clear()
    EVENT_LOG.clear()
    NARWHAL_STORE.clear()
    HOTSTUFF_STORE.clear()
    SWIM_STORE.clear()
    FAULT_STORE.clear()
    REPLAY_GUARD.clear()
    EQUIVOCATION_DETECTOR.clear()
    CHECKPOINT_STORE.clear()
    RECOVERY_STORE.clear()
    NODE_KEY_REGISTRY.clear()
    BFT_METRICS.reset_for_tests()


def _minimal_bft_client() -> TestClient:
    _configure_bft_router_for_security_tests()
    app = FastAPI(title="Security BFT test app")
    app.include_router(bft_router)
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_security_bft_state():
    _clear_bft_state()
    _configure_bft_router_for_security_tests()
    yield
    _clear_bft_state()


@pytest.fixture
def security_bft_client() -> TestClient:
    return _minimal_bft_client()


@pytest.fixture
def security_full_app_client() -> TestClient:
    _configure_bft_router_for_security_tests()
    try:
        main = importlib.import_module("vetclinic_api.main")
        return TestClient(main.app)
    except Exception:
        return _minimal_bft_client()


@pytest.fixture
def security_headers() -> dict[str, str]:
    return {"Authorization": "Bearer demo-security-token"}


@pytest.fixture
def invalid_security_headers() -> dict[str, str]:
    return {"Authorization": "Bearer invalid-token"}


@pytest.fixture
def sample_operation_payload() -> dict:
    return {
        "sender": "security-alice",
        "recipient": "security-bob",
        "amount": 10.5,
        "payload": {"kind": "security-smoke"},
    }

