from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

API_PATH = Path(__file__).resolve().parents[2] / "VetClinic" / "API"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from vetclinic_api.bft.common.events import EVENT_LOG  # noqa: E402
from vetclinic_api.bft.common.operations import (  # noqa: E402
    OPERATION_STORE,
    ClientOperationInput,
)
from vetclinic_api.bft.crypto.envelope import BftMessagePayload  # noqa: E402
from vetclinic_api.bft.crypto.registry import NODE_KEY_REGISTRY  # noqa: E402
from vetclinic_api.bft.crypto.service import CryptoService  # noqa: E402
from vetclinic_api.bft.checkpointing.service import CheckpointService  # noqa: E402
from vetclinic_api.bft.checkpointing.store import CHECKPOINT_STORE  # noqa: E402
from vetclinic_api.bft.fault_injection.equivocation import (  # noqa: E402
    EQUIVOCATION_DETECTOR,
)
from vetclinic_api.bft.fault_injection.replay import REPLAY_GUARD  # noqa: E402
from vetclinic_api.bft.fault_injection.service import FaultInjectionService  # noqa: E402
from vetclinic_api.bft.fault_injection.store import FAULT_STORE  # noqa: E402
from vetclinic_api.bft.hotstuff.store import HOTSTUFF_STORE  # noqa: E402
from vetclinic_api.bft.narwhal.store import NARWHAL_STORE  # noqa: E402
from vetclinic_api.bft.observability.health import HealthService  # noqa: E402
from vetclinic_api.bft.observability.metrics import BFT_METRICS  # noqa: E402
from vetclinic_api.bft.observability.scenarios import BftDemoScenarioRunner  # noqa: E402
from vetclinic_api.bft.recovery.service import RecoveryService  # noqa: E402
from vetclinic_api.bft.recovery.store import RECOVERY_STORE  # noqa: E402
from vetclinic_api.bft.swim.store import SWIM_STORE  # noqa: E402
import vetclinic_api.routers.bft as bft_module  # noqa: E402
from vetclinic_api.routers.bft import router as bft_router  # noqa: E402


def _clear_all() -> None:
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


@pytest.fixture(autouse=True)
def clean_bft_state():
    _clear_all()
    yield
    _clear_all()


@pytest.fixture
def operation_store():
    return OPERATION_STORE


@pytest.fixture
def event_log():
    return EVENT_LOG


@pytest.fixture
def narwhal_store():
    return NARWHAL_STORE


@pytest.fixture
def hotstuff_store():
    return HOTSTUFF_STORE


@pytest.fixture
def swim_store():
    return SWIM_STORE


@pytest.fixture
def fault_store():
    return FAULT_STORE


@pytest.fixture
def fault_service():
    return FaultInjectionService(FAULT_STORE, EVENT_LOG)


@pytest.fixture
def replay_guard():
    return REPLAY_GUARD


@pytest.fixture
def equivocation_detector():
    return EQUIVOCATION_DETECTOR


@pytest.fixture
def checkpoint_store():
    return CHECKPOINT_STORE


@pytest.fixture
def checkpoint_service():
    return CheckpointService(OPERATION_STORE, CHECKPOINT_STORE, EVENT_LOG)


@pytest.fixture
def recovery_store():
    return RECOVERY_STORE


@pytest.fixture
def recovery_service():
    return RecoveryService(
        OPERATION_STORE,
        CHECKPOINT_STORE,
        RECOVERY_STORE,
        SWIM_STORE,
        EVENT_LOG,
    )


@pytest.fixture
def node_key_registry():
    return NODE_KEY_REGISTRY


@pytest.fixture
def crypto_service():
    return CryptoService(NODE_KEY_REGISTRY, REPLAY_GUARD, EVENT_LOG)


@pytest.fixture
def signed_message_factory(crypto_service):
    def factory(payload: BftMessagePayload, source_node_id: int):
        NODE_KEY_REGISTRY.ensure_demo_keys([source_node_id])
        return crypto_service.sign_message(payload, source_node_id)

    return factory


@pytest.fixture
def bft_metrics():
    return BFT_METRICS


@pytest.fixture
def health_service():
    return HealthService(
        operation_store=OPERATION_STORE,
        narwhal_store=NARWHAL_STORE,
        hotstuff_store=HOTSTUFF_STORE,
        swim_store=SWIM_STORE,
        fault_store=FAULT_STORE,
        checkpoint_store=CHECKPOINT_STORE,
        recovery_store=RECOVERY_STORE,
        node_key_registry=NODE_KEY_REGISTRY,
        self_node_id=1,
    )


@pytest.fixture
def demo_runner(
    bft_metrics,
    health_service,
):
    return BftDemoScenarioRunner(
        operation_store=OPERATION_STORE,
        narwhal_service=bft_module.NARWHAL_SERVICE,
        hotstuff_service=bft_module.HOTSTUFF_SERVICE,
        swim_service=bft_module.SWIM_SERVICE,
        fault_service=bft_module.FAULT_SERVICE,
        checkpoint_service=bft_module.CHECKPOINT_SERVICE,
        recovery_service=bft_module.RECOVERY_SERVICE,
        crypto_service=bft_module.CRYPTO_SERVICE,
        event_log=EVENT_LOG,
        metrics=bft_metrics,
        health_service=health_service,
    )


@pytest.fixture
def sample_operation_input():
    return ClientOperationInput(
        sender="alice",
        recipient="bob",
        amount=10.5,
        payload={"kind": "testbed"},
    )


@pytest.fixture
def total_nodes_6():
    return 6


@pytest.fixture
def bft_client():
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
    app = FastAPI()
    app.include_router(bft_router)
    return TestClient(app)
