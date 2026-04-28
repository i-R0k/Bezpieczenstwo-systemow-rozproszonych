from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query, Response
from pydantic import BaseModel, Field

from vetclinic_api.bft import apply_fastapi_compat
from vetclinic_api.bft.checkpointing.models import (
    CheckpointCertificate,
    CheckpointCertifyRequest,
    CheckpointCreateRequest,
    CheckpointStatus,
    StateSnapshot,
)
from vetclinic_api.bft.checkpointing.service import CheckpointService
from vetclinic_api.bft.checkpointing.store import CHECKPOINT_STORE
from vetclinic_api.bft.common.events import EVENT_LOG, ProtocolEvent
from vetclinic_api.bft.common.operations import (
    OPERATION_STORE,
    ClientOperation,
    ClientOperationInput,
    OperationTrace,
)
from vetclinic_api.bft.common.quorum import describe_quorum
from vetclinic_api.bft.common.types import (
    FaultType,
    MessageKind,
    NodeStatus,
    OperationStatus,
    ProtocolName,
)
from vetclinic_api.bft.crypto.envelope import (
    BftMessagePayload,
    BftSignedMessage,
    BftVerificationResult,
)
from vetclinic_api.bft.crypto.registry import NODE_KEY_REGISTRY
from vetclinic_api.bft.crypto.service import CRYPTO_SERVICE
from vetclinic_api.bft.fault_injection.equivocation import EQUIVOCATION_DETECTOR
from vetclinic_api.bft.fault_injection.models import (
    FaultDecision,
    FaultEvaluationContext,
    FaultInjectionStatus,
    FaultRule,
    InjectedFault,
    NetworkPartition,
)
from vetclinic_api.bft.fault_injection.replay import REPLAY_GUARD
from vetclinic_api.bft.fault_injection.service import FaultInjectionService
from vetclinic_api.bft.fault_injection.store import FAULT_STORE
from vetclinic_api.bft.hotstuff.models import (
    CommitCertificate,
    HotStuffProposal,
    HotStuffStatus,
    QuorumCertificate,
    ViewState,
)
from vetclinic_api.bft.hotstuff.service import HotStuffService
from vetclinic_api.bft.hotstuff.store import HOTSTUFF_STORE
from vetclinic_api.bft.narwhal.models import (
    BatchCertificate,
    NarwhalBatch,
    NarwhalBatchRequest,
    NarwhalBatchResponse,
    NarwhalDagView,
)
from vetclinic_api.bft.narwhal.service import NarwhalService
from vetclinic_api.bft.narwhal.store import NARWHAL_STORE
from vetclinic_api.bft.observability.health import BftSystemHealth, HealthService
from vetclinic_api.bft.observability.metrics import BFT_METRICS
from vetclinic_api.bft.observability.report import BftDemoReport
from vetclinic_api.bft.observability.scenarios import BftDemoScenarioRunner
from vetclinic_api.bft.recovery.models import (
    RecoveryResult,
    RecoveryStatus,
    StateTransferRequest,
    StateTransferResponse,
)
from vetclinic_api.bft.recovery.service import RecoveryService
from vetclinic_api.bft.recovery.store import RECOVERY_STORE
from vetclinic_api.bft.swim.models import (
    SwimAck,
    SwimGossipEnvelope,
    SwimMember,
    SwimProbeResult,
    SwimStatus,
)
from vetclinic_api.bft.swim.service import SwimService
from vetclinic_api.bft.swim.store import SWIM_STORE
from vetclinic_api.cluster.config import CONFIG

apply_fastapi_compat()

router = APIRouter(prefix="/bft", tags=["bft"])
if not hasattr(router, "on_startup"):
    router.on_startup = []
if not hasattr(router, "on_shutdown"):
    router.on_shutdown = []
FAULT_SERVICE = FaultInjectionService(FAULT_STORE, EVENT_LOG)
NARWHAL_SERVICE = NarwhalService(
    OPERATION_STORE,
    EVENT_LOG,
    NARWHAL_STORE,
    FAULT_SERVICE,
    CRYPTO_SERVICE,
)
HOTSTUFF_SERVICE = HotStuffService(
    OPERATION_STORE,
    EVENT_LOG,
    NARWHAL_STORE,
    HOTSTUFF_STORE,
    SWIM_STORE,
    FAULT_SERVICE,
    CRYPTO_SERVICE,
)
SWIM_SERVICE = SwimService(SWIM_STORE, EVENT_LOG, FAULT_SERVICE, CRYPTO_SERVICE)
CHECKPOINT_SERVICE = CheckpointService(
    OPERATION_STORE,
    CHECKPOINT_STORE,
    EVENT_LOG,
    CRYPTO_SERVICE,
)
RECOVERY_SERVICE = RecoveryService(
    OPERATION_STORE,
    CHECKPOINT_STORE,
    RECOVERY_STORE,
    SWIM_STORE,
    EVENT_LOG,
    CRYPTO_SERVICE,
)
LAST_DEMO_REPORT: BftDemoReport | None = None


class NarwhalAckRequest(BaseModel):
    node_id: int | None = None
    accepted: bool = True
    reason: str | None = None


class HotStuffProposalRequest(BaseModel):
    batch_id: str
    proposer_node_id: int | None = None


class HotStuffVoteRequest(BaseModel):
    voter_node_id: int | None = None
    accepted: bool = True
    reason: str | None = None


class HotStuffViewChangeRequest(BaseModel):
    reason: str = "demo_timeout"


class SwimPingReqRequest(BaseModel):
    intermediary_node_id: int
    target_node_id: int
    simulate_success: bool = True


class SwimProbeDemoRequest(BaseModel):
    fail_direct: bool = False
    fail_indirect: bool = False


class FaultRuleRequest(BaseModel):
    fault_type: FaultType
    protocol: ProtocolName | None = None
    source_node_id: int | None = None
    target_node_id: int | None = None
    message_kind: MessageKind | None = None
    probability: float = 1.0
    delay_ms: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NetworkPartitionRequest(BaseModel):
    groups: list[list[int]]


class StateTransferCreateRequest(BaseModel):
    node_id: int
    checkpoint_id: str | None = None
    reason: str = "stale_or_crashed_node"


class CryptoSignRequest(BaseModel):
    protocol: ProtocolName
    message_kind: MessageKind
    source_node_id: int
    target_node_id: int | None = None
    operation_id: str | None = None
    correlation_id: str | None = None
    body: dict[str, Any] = Field(default_factory=dict)


def _node_count() -> int:
    return 1 + len(CONFIG.peers)


def _health_service() -> HealthService:
    return HealthService(
        operation_store=OPERATION_STORE,
        narwhal_store=NARWHAL_STORE,
        hotstuff_store=HOTSTUFF_STORE,
        swim_store=SWIM_STORE,
        fault_store=FAULT_STORE,
        checkpoint_store=CHECKPOINT_STORE,
        recovery_store=RECOVERY_STORE,
        node_key_registry=NODE_KEY_REGISTRY,
        self_node_id=CONFIG.node_id,
    )


def _refresh_metric_gauges() -> dict[str, float]:
    return BFT_METRICS.refresh_gauges(
        operation_store=OPERATION_STORE,
        narwhal_store=NARWHAL_STORE,
        hotstuff_store=HOTSTUFF_STORE,
        swim_store=SWIM_STORE,
        fault_store=FAULT_STORE,
        checkpoint_store=CHECKPOINT_STORE,
        recovery_store=RECOVERY_STORE,
        node_key_registry=NODE_KEY_REGISTRY,
        self_node_id=CONFIG.node_id,
    )


def _demo_runner() -> BftDemoScenarioRunner:
    return BftDemoScenarioRunner(
        operation_store=OPERATION_STORE,
        narwhal_service=NARWHAL_SERVICE,
        hotstuff_service=HOTSTUFF_SERVICE,
        swim_service=SWIM_SERVICE,
        fault_service=FAULT_SERVICE,
        checkpoint_service=CHECKPOINT_SERVICE,
        recovery_service=RECOVERY_SERVICE,
        crypto_service=CRYPTO_SERVICE,
        event_log=EVENT_LOG,
        metrics=BFT_METRICS,
        health_service=_health_service(),
    )


def _append_protocol_event(
    *,
    protocol: ProtocolName,
    operation_id: str | None,
    status: OperationStatus | None,
    message: str,
    details: dict[str, Any] | None = None,
    node_id: int | None = None,
) -> None:
    EVENT_LOG.append(
        ProtocolEvent(
            event_id=str(uuid.uuid4()),
            node_id=node_id if node_id is not None else CONFIG.node_id,
            protocol=protocol,
            operation_id=operation_id,
            status=status,
            message=message,
            details=details or {},
        )
    )


def _transition_operation(
    operation_id: str,
    *,
    to_status: OperationStatus,
    protocol: ProtocolName,
    message: str,
    details: dict[str, Any] | None = None,
) -> ClientOperation:
    try:
        operation = OPERATION_STORE.transition(
            operation_id=operation_id,
            to_status=to_status,
            protocol=protocol,
            message=message,
            node_id=CONFIG.node_id,
            details=details,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    _append_protocol_event(
        protocol=protocol,
        operation_id=operation_id,
        status=to_status,
        message=message,
        details=details,
    )
    return operation


def _handle_narwhal_error(exc: Exception) -> None:
    if isinstance(exc, KeyError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    raise exc


def _handle_hotstuff_error(exc: Exception) -> None:
    if isinstance(exc, KeyError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    raise exc


def _handle_fault_error(exc: Exception) -> None:
    if isinstance(exc, KeyError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise exc


def _find_batch_id_for_operation(operation_id: str) -> str | None:
    batch = HOTSTUFF_SERVICE.find_batch_by_operation_id(operation_id)
    return batch.batch_id if batch else None


def is_node_eligible_for_consensus(node_id: int) -> bool:
    try:
        member = SWIM_STORE.get_member(node_id)
    except KeyError:
        return True
    return member.status == NodeStatus.ALIVE


def _ensure_consensus_eligible(node_id: int, role: str) -> None:
    if not is_node_eligible_for_consensus(node_id):
        member = SWIM_STORE.get_member(node_id)
        raise HTTPException(
            status_code=409,
            detail=f"{role} node {node_id} is not eligible for consensus: {member.status.value}",
        )


@router.get("/architecture")
def architecture() -> dict:
    swim_status = SWIM_SERVICE.status(CONFIG.node_id)
    fault_status = FAULT_SERVICE.status()
    checkpoint_status = CHECKPOINT_SERVICE.status()
    recovery_status = RECOVERY_SERVICE.status()
    global LAST_DEMO_REPORT
    return {
        "stage": "final-bft-demonstrator",
        "status": "demonstracyjna implementacja in-memory",
        "description": (
            "BFT layer exposes demonstracyjne, in-memory kontrakty Narwhal, "
            "HotStuff, SWIM, fault injection, checkpointing, recovery, crypto "
            "i observability. VetClinic remains the sample application domain."
        ),
        "boundaries": {
            "domain": "VetClinic models, CRUD, services, and legacy blockchain endpoints",
            "bft": "demonstracyjne protocol contracts, event log, quorum math, and in-memory protocol modules",
            "api": "FastAPI routers exposing stable external contracts",
            "ops": "fault injection, Prometheus, Grafana, and scenario scripts",
        },
        "swim_membership": {
            "bootstrapped": len(swim_status.members) > 0,
            "alive": swim_status.alive,
            "suspect": swim_status.suspect,
            "dead": swim_status.dead,
            "recovering": swim_status.recovering,
        },
        "fault_injection": {
            "rules_count": len(fault_status.rules),
            "partitions_count": len(fault_status.partitions),
            "injected_faults_count": len(fault_status.injected_faults),
            "counters": fault_status.counters,
        },
        "checkpointing": {
            "snapshots_count": len(checkpoint_status.snapshots),
            "certificates_count": len(checkpoint_status.certificates),
            "latest_checkpoint_id": checkpoint_status.latest_certificate.checkpoint_id
            if checkpoint_status.latest_certificate
            else None,
        },
        "recovery": {
            "state_transfers_count": len(recovery_status.transfers),
            "recovered_nodes_count": len(recovery_status.recovered_nodes),
        },
        "crypto": {
            "registered_public_keys_count": len(NODE_KEY_REGISTRY.public_keys()),
            "replay_guard_enabled": True,
            "signed_message_support": True,
        },
        "observability": {
            "metrics_enabled": True,
            "health_endpoint": "/bft/observability/health",
            "demo_runner_available": True,
            "last_demo_status": LAST_DEMO_REPORT.status if LAST_DEMO_REPORT else None,
        },
    }


@router.get("/protocols")
def protocols() -> dict:
    implementation_level = "demonstracyjna, in-memory"
    return {
        "protocols": [
            {
                "name": "Narwhal",
                "scope": "batching, DAG, data availability, batch certificate",
                "implemented": True,
                "implementation_level": implementation_level,
                "limitations": "local in-memory DAG and local demo certification, no production network broadcast",
            },
            {
                "name": "HotStuff",
                "scope": "proposal, vote, quorum certificate, commit, view-change",
                "implemented": True,
                "implementation_level": implementation_level,
                "limitations": "local demo QC/view-change, no production multi-process consensus pipeline",
            },
            {
                "name": "SWIM",
                "scope": "membership, alive/suspect/dead detection",
                "implemented": True,
                "implementation_level": implementation_level,
                "limitations": "logical in-memory membership, no full distributed gossip transport",
            },
            {
                "name": "Fault Injection",
                "scope": "controlled drop, delay, duplicate, replay, equivocation, partition, leader failure",
                "implemented": True,
                "implementation_level": implementation_level,
                "limitations": "deterministic local decisions; delay does not sleep in tests",
            },
            {
                "name": "Checkpointing",
                "scope": "state snapshots, state hash, checkpoint certificate",
                "implemented": True,
                "implementation_level": implementation_level,
                "limitations": "snapshots and certificates are in-memory",
            },
            {
                "name": "Recovery",
                "scope": "state transfer, apply checkpoint, node catch-up",
                "implemented": True,
                "implementation_level": implementation_level,
                "limitations": "state transfer is modeled locally",
            },
            {
                "name": "Crypto",
                "scope": "Ed25519 signing, canonical JSON, nonce, message_id, replay protection",
                "implemented": True,
                "implementation_level": implementation_level,
                "limitations": "demo keys are in-memory; mTLS is not production-configured",
            },
            {
                "name": "Observability",
                "scope": "health, Prometheus text metrics, metrics snapshot, demo report",
                "implemented": True,
                "implementation_level": implementation_level,
                "limitations": "Prometheus/Grafana are optional; testbed uses local metrics snapshot",
            },
        ]
    }


def _status_section(name: str, producer) -> dict:
    try:
        payload = producer()
        if isinstance(payload, dict):
            return {"status": "ok", **payload}
        return {"status": "ok", "value": payload}
    except Exception as exc:
        return {"status": "error", "error": str(exc), "section": name}


@router.get("/status")
def bft_status() -> dict:
    return {
        "status": "ok",
        "architecture": _status_section(
            "architecture",
            lambda: {
                "stage": "final-bft-demonstrator",
                "implementation_level": "demonstracyjna, in-memory",
                "router": "/bft",
            },
        ),
        "quorum": _status_section(
            "quorum",
            lambda: {
                "summary": describe_quorum(_node_count()),
                "self": CONFIG.node_id,
                "peers": CONFIG.peers,
            },
        ),
        "operations": _status_section(
            "operations",
            lambda: {"count": len(OPERATION_STORE.list(limit=10_000))},
        ),
        "narwhal": _status_section(
            "narwhal",
            lambda: {
                "batch_count": len(NARWHAL_STORE.list_batches(limit=10_000)),
                "dag_total_batches": NARWHAL_STORE.get_dag().total_batches,
                "tips_count": len(NARWHAL_STORE.get_tips()),
            },
        ),
        "hotstuff": _status_section(
            "hotstuff",
            lambda: {
                "proposal_count": len(HOTSTUFF_STORE.list_proposals(limit=10_000)),
                "qc_count": len(HOTSTUFF_STORE.list_qcs(limit=10_000)),
                "commit_count": len(HOTSTUFF_STORE.list_commits(limit=10_000)),
                "view": HOTSTUFF_STORE.current_view().view,
            },
        ),
        "swim": _status_section(
            "swim",
            lambda: {
                "alive": SWIM_SERVICE.status(CONFIG.node_id).alive,
                "suspect": SWIM_SERVICE.status(CONFIG.node_id).suspect,
                "dead": SWIM_SERVICE.status(CONFIG.node_id).dead,
                "recovering": SWIM_SERVICE.status(CONFIG.node_id).recovering,
            },
        ),
        "fault_injection": _status_section(
            "fault_injection",
            lambda: {
                "rules_count": len(FAULT_STORE.list_rules()),
                "partitions_count": len(FAULT_STORE.list_partitions()),
                "injected_count": len(FAULT_STORE.list_injected_faults(limit=10_000)),
                "counters": FAULT_STORE.counters(),
            },
        ),
        "checkpointing": _status_section(
            "checkpointing",
            lambda: {
                "snapshots_count": len(CHECKPOINT_STORE.list_snapshots(limit=10_000)),
                "certificates_count": len(CHECKPOINT_STORE.list_certificates(limit=10_000)),
                "latest_checkpoint_id": CHECKPOINT_STORE.latest_certificate().checkpoint_id
                if CHECKPOINT_STORE.latest_certificate()
                else None,
            },
        ),
        "recovery": _status_section(
            "recovery",
            lambda: {
                "state_transfers_count": len(RECOVERY_STORE.status().transfers),
                "recovered_nodes_count": len(RECOVERY_STORE.status().recovered_nodes),
            },
        ),
        "crypto": _status_section(
            "crypto",
            lambda: {
                "registered_public_keys_count": len(NODE_KEY_REGISTRY.public_keys()),
                "replay_guard_enabled": True,
            },
        ),
        "observability": _status_section(
            "observability",
            lambda: {
                "metrics_enabled": True,
                "metrics_snapshot": BFT_METRICS.snapshot(),
                "last_demo_status": LAST_DEMO_REPORT.status if LAST_DEMO_REPORT else None,
            },
        ),
    }


@router.get("/quorum")
def quorum() -> dict:
    node_count = _node_count()
    try:
        summary = describe_quorum(node_count)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        **summary,
        "total_nodes": summary["nodes"],
        "quorum_size": summary["quorum"],
        "self": CONFIG.node_id,
        "peers": CONFIG.peers,
    }


@router.get("/events")
def list_events(limit: int = Query(default=100, ge=0)) -> dict:
    return {
        "events": EVENT_LOG.list(limit=limit),
        "limit": limit,
    }


@router.delete("/events")
def clear_events() -> dict:
    EVENT_LOG.clear()
    return {"status": "cleared"}


@router.get("/observability/health", response_model=BftSystemHealth)
def observability_health() -> BftSystemHealth:
    return _health_service().check_all()


@router.get("/observability/metrics")
def observability_metrics() -> Response:
    _refresh_metric_gauges()
    return Response(
        content=BFT_METRICS.export_latest_text(),
        media_type="text/plain; version=0.0.4",
    )


@router.get("/observability/metrics/snapshot")
def observability_metrics_snapshot() -> dict:
    return {
        "gauges_refreshed": _refresh_metric_gauges(),
        **BFT_METRICS.snapshot(),
    }


@router.post("/demo/run", response_model=BftDemoReport)
def run_bft_demo() -> BftDemoReport:
    global LAST_DEMO_REPORT
    LAST_DEMO_REPORT = _demo_runner().run_full_demo(total_nodes=_node_count())
    return LAST_DEMO_REPORT


@router.get("/demo/last-report", response_model=BftDemoReport)
def get_last_bft_demo_report() -> BftDemoReport:
    if LAST_DEMO_REPORT is None:
        raise HTTPException(status_code=404, detail="No demo report available")
    return LAST_DEMO_REPORT


@router.delete("/demo/last-report")
def clear_last_bft_demo_report() -> dict:
    global LAST_DEMO_REPORT
    LAST_DEMO_REPORT = None
    return {"status": "cleared"}


@router.post("/crypto/demo-keys")
def create_crypto_demo_keys(
    total_nodes: int | None = Query(default=None, ge=1),
) -> dict:
    keys = CRYPTO_SERVICE.ensure_demo_keys(total_nodes or _node_count())
    return {
        "public_keys": {
            key.node_id: key.public_key_b64
            for key in keys
        }
    }


@router.get("/crypto/public-keys")
def crypto_public_keys() -> dict:
    return {"public_keys": NODE_KEY_REGISTRY.public_keys()}


@router.post("/crypto/sign", response_model=BftSignedMessage)
def crypto_sign(request: CryptoSignRequest) -> BftSignedMessage:
    try:
        NODE_KEY_REGISTRY.ensure_demo_keys([request.source_node_id])
        return CRYPTO_SERVICE.sign_message(
            BftMessagePayload(
                protocol=request.protocol,
                message_kind=request.message_kind,
                source_node_id=request.source_node_id,
                target_node_id=request.target_node_id,
                operation_id=request.operation_id,
                correlation_id=request.correlation_id,
                body=request.body,
            ),
            request.source_node_id,
        )
    except KeyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/crypto/verify", response_model=BftVerificationResult)
def crypto_verify(message: BftSignedMessage) -> BftVerificationResult:
    return CRYPTO_SERVICE.verify_message(message)


@router.post("/crypto/verify/{protocol}", response_model=BftVerificationResult)
def crypto_verify_protocol(
    protocol: ProtocolName,
    message: BftSignedMessage,
    expected_kind: MessageKind | None = Query(default=None),
) -> BftVerificationResult:
    return CRYPTO_SERVICE.verify_message_for_protocol(
        message,
        expected_protocol=protocol,
        expected_kind=expected_kind,
    )


@router.delete("/crypto")
def clear_crypto() -> dict:
    CRYPTO_SERVICE.clear()
    return {"status": "cleared"}


@router.post("/faults/rules", response_model=FaultRule)
def create_fault_rule(request: FaultRuleRequest) -> FaultRule:
    try:
        return FAULT_SERVICE.create_rule(
            fault_type=request.fault_type,
            protocol=request.protocol,
            source_node_id=request.source_node_id,
            target_node_id=request.target_node_id,
            message_kind=request.message_kind,
            probability=request.probability,
            delay_ms=request.delay_ms,
            metadata=request.metadata,
        )
    except Exception as exc:
        _handle_fault_error(exc)
        raise


@router.get("/faults/rules")
def list_fault_rules() -> dict:
    return {"rules": FAULT_STORE.list_rules()}


@router.get("/faults/rules/{rule_id}", response_model=FaultRule)
def get_fault_rule(rule_id: str) -> FaultRule:
    try:
        return FAULT_STORE.get_rule(rule_id)
    except Exception as exc:
        _handle_fault_error(exc)
        raise


@router.put("/faults/rules/{rule_id}/enable", response_model=FaultRule)
def enable_fault_rule(rule_id: str) -> FaultRule:
    try:
        return FAULT_STORE.enable_rule(rule_id)
    except Exception as exc:
        _handle_fault_error(exc)
        raise


@router.put("/faults/rules/{rule_id}/disable", response_model=FaultRule)
def disable_fault_rule(rule_id: str) -> FaultRule:
    try:
        return FAULT_STORE.disable_rule(rule_id)
    except Exception as exc:
        _handle_fault_error(exc)
        raise


@router.delete("/faults/rules/{rule_id}")
def delete_fault_rule(rule_id: str) -> dict:
    try:
        FAULT_STORE.delete_rule(rule_id)
        return {"status": "deleted", "rule_id": rule_id}
    except Exception as exc:
        _handle_fault_error(exc)
        raise


@router.post("/faults/partitions", response_model=NetworkPartition)
def create_fault_partition(request: NetworkPartitionRequest) -> NetworkPartition:
    try:
        return FAULT_SERVICE.create_partition(request.groups)
    except Exception as exc:
        _handle_fault_error(exc)
        raise


@router.get("/faults/partitions")
def list_fault_partitions() -> dict:
    return {"partitions": FAULT_STORE.list_partitions()}


@router.put("/faults/partitions/{partition_id}/enable", response_model=NetworkPartition)
def enable_fault_partition(partition_id: str) -> NetworkPartition:
    try:
        return FAULT_STORE.enable_partition(partition_id)
    except Exception as exc:
        _handle_fault_error(exc)
        raise


@router.put("/faults/partitions/{partition_id}/disable", response_model=NetworkPartition)
def disable_fault_partition(partition_id: str) -> NetworkPartition:
    try:
        return FAULT_STORE.disable_partition(partition_id)
    except Exception as exc:
        _handle_fault_error(exc)
        raise


@router.delete("/faults/partitions/{partition_id}")
def delete_fault_partition(partition_id: str) -> dict:
    try:
        FAULT_STORE.delete_partition(partition_id)
        return {"status": "deleted", "partition_id": partition_id}
    except Exception as exc:
        _handle_fault_error(exc)
        raise


@router.post("/faults/evaluate", response_model=FaultDecision)
def evaluate_faults(context: FaultEvaluationContext) -> FaultDecision:
    return FAULT_SERVICE.evaluate(context)


@router.get("/faults/status", response_model=FaultInjectionStatus)
def fault_status() -> FaultInjectionStatus:
    return FAULT_SERVICE.status()


@router.get("/faults/injected")
def list_injected_faults(limit: int = Query(default=100, ge=0)) -> dict:
    return {"injected_faults": FAULT_STORE.list_injected_faults(limit=limit)}


@router.get("/faults/equivocation/conflicts")
def list_equivocation_conflicts() -> dict:
    return {"conflicts": EQUIVOCATION_DETECTOR.list_conflicts()}


@router.delete("/faults")
def clear_faults() -> dict:
    FAULT_SERVICE.clear()
    REPLAY_GUARD.clear()
    EQUIVOCATION_DETECTOR.clear()
    return {"status": "cleared"}


@router.post("/checkpointing/snapshots", response_model=StateSnapshot)
def create_checkpoint_snapshot(
    payload: CheckpointCreateRequest | None = Body(default=None),
) -> StateSnapshot:
    return CHECKPOINT_SERVICE.create_snapshot(
        node_id=payload.node_id if payload and payload.node_id is not None else CONFIG.node_id
    )


@router.get("/checkpointing/snapshots")
def list_checkpoint_snapshots(limit: int = Query(default=100, ge=0)) -> dict:
    return {"snapshots": CHECKPOINT_STORE.list_snapshots(limit=limit)}


@router.get("/checkpointing/snapshots/{snapshot_id}", response_model=StateSnapshot)
def get_checkpoint_snapshot(snapshot_id: str) -> StateSnapshot:
    try:
        return CHECKPOINT_STORE.get_snapshot(snapshot_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/checkpointing/snapshots/{snapshot_id}/certify",
    response_model=CheckpointCertificate,
)
def certify_checkpoint_snapshot(
    snapshot_id: str,
    payload: CheckpointCertifyRequest | None = Body(default=None),
) -> CheckpointCertificate:
    try:
        return CHECKPOINT_SERVICE.certify_snapshot(
            snapshot_id=snapshot_id,
            total_nodes=_node_count(),
            signer_node_ids=payload.signer_node_ids if payload else None,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/checkpointing/certificates/{checkpoint_id}", response_model=CheckpointCertificate)
def get_checkpoint_certificate(checkpoint_id: str) -> CheckpointCertificate:
    try:
        return CHECKPOINT_STORE.get_certificate(checkpoint_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/checkpointing/status", response_model=CheckpointStatus)
def checkpointing_status() -> CheckpointStatus:
    return CHECKPOINT_SERVICE.status()


@router.delete("/checkpointing")
def clear_checkpointing() -> dict:
    CHECKPOINT_SERVICE.clear()
    return {"status": "cleared"}


@router.post("/recovery/state-transfer", response_model=StateTransferRequest)
def request_state_transfer(request: StateTransferCreateRequest) -> StateTransferRequest:
    try:
        return RECOVERY_SERVICE.request_state_transfer(
            node_id=request.node_id,
            checkpoint_id=request.checkpoint_id,
            reason=request.reason,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/recovery/state-transfer/{node_id}/response", response_model=StateTransferResponse)
def build_state_transfer_response(node_id: int) -> StateTransferResponse:
    try:
        transfer = next(
            request
            for request in reversed(RECOVERY_SERVICE.status().transfers)
            if request.node_id == node_id
        )
    except StopIteration as exc:
        raise HTTPException(status_code=404, detail=f"State transfer not found for node {node_id}") from exc
    return RECOVERY_SERVICE.build_state_transfer_response(transfer)


@router.post("/recovery/nodes/{node_id}/apply", response_model=RecoveryResult)
def apply_state_transfer(node_id: int) -> RecoveryResult:
    try:
        transfer = next(
            request
            for request in reversed(RECOVERY_SERVICE.status().transfers)
            if request.node_id == node_id
        )
    except StopIteration as exc:
        raise HTTPException(status_code=404, detail=f"State transfer not found for node {node_id}") from exc
    try:
        return RECOVERY_SERVICE.apply_state_transfer(transfer)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/recovery/nodes/{node_id}/recover-demo", response_model=RecoveryResult)
def recover_node_demo(
    node_id: int,
    checkpoint_id: str | None = Query(default=None),
) -> RecoveryResult:
    try:
        return RECOVERY_SERVICE.recover_node(
            node_id=node_id,
            checkpoint_id=checkpoint_id,
            reason="recover-demo",
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/recovery/status", response_model=RecoveryStatus)
def recovery_status() -> RecoveryStatus:
    return RECOVERY_SERVICE.status()


@router.delete("/recovery")
def clear_recovery() -> dict:
    RECOVERY_SERVICE.clear()
    return {"status": "cleared"}


@router.post("/narwhal/batches", response_model=NarwhalBatchResponse)
def create_narwhal_batch(request: NarwhalBatchRequest) -> NarwhalBatchResponse:
    try:
        return NARWHAL_SERVICE.create_batch_from_operations(
            author_node_id=CONFIG.node_id,
            total_nodes=_node_count(),
            operation_ids=request.operation_ids,
            max_operations=request.max_operations,
        )
    except Exception as exc:
        _handle_narwhal_error(exc)
        raise


@router.get("/narwhal/batches")
def list_narwhal_batches(limit: int = Query(default=100, ge=0)) -> dict:
    return {
        "batches": NARWHAL_STORE.list_batches(limit=limit),
        "limit": limit,
    }


@router.get("/narwhal/batches/{batch_id}", response_model=NarwhalBatch)
def get_narwhal_batch(batch_id: str) -> NarwhalBatch:
    try:
        return NARWHAL_STORE.get_batch(batch_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/narwhal/batches/{batch_id}/ack")
def acknowledge_narwhal_batch(
    batch_id: str,
    payload: NarwhalAckRequest | None = Body(default=None),
    node_id: int | None = Query(default=None),
    accepted: bool | None = Query(default=None),
    reason: str | None = Query(default=None),
) -> dict:
    resolved_node_id = (
        node_id
        if node_id is not None
        else payload.node_id
        if payload and payload.node_id is not None
        else CONFIG.node_id
    )
    resolved_accepted = (
        accepted
        if accepted is not None
        else payload.accepted
        if payload
        else True
    )
    resolved_reason = reason if reason is not None else payload.reason if payload else None
    try:
        certificate = NARWHAL_SERVICE.acknowledge_batch(
            batch_id=batch_id,
            node_id=resolved_node_id,
            accepted=resolved_accepted,
            reason=resolved_reason,
            total_nodes=_node_count(),
        )
    except Exception as exc:
        _handle_narwhal_error(exc)
        raise

    if certificate:
        return {
            "status": "certified",
            "certificate": certificate,
        }
    return {
        "status": "acknowledged",
        "certificate": None,
        "detail": "Quorum not reached yet",
    }


@router.post(
    "/narwhal/batches/{batch_id}/certify-demo",
    response_model=BatchCertificate,
)
def certify_narwhal_batch_demo(batch_id: str) -> BatchCertificate:
    try:
        certificate = NARWHAL_SERVICE.certify_batch_locally(
            batch_id=batch_id,
            total_nodes=_node_count(),
        )
    except Exception as exc:
        _handle_narwhal_error(exc)
        raise
    if not certificate:
        raise HTTPException(status_code=409, detail="Quorum not reached")
    return certificate


@router.get(
    "/narwhal/batches/{batch_id}/certificate",
    response_model=BatchCertificate,
)
def get_narwhal_batch_certificate(batch_id: str) -> BatchCertificate:
    try:
        certificate = NARWHAL_STORE.get_certificate(batch_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not certificate:
        raise HTTPException(status_code=404, detail="Batch certificate not found")
    return certificate


@router.get("/narwhal/dag", response_model=NarwhalDagView)
def get_narwhal_dag() -> NarwhalDagView:
    return NARWHAL_SERVICE.get_dag()


@router.get("/narwhal/tips")
def get_narwhal_tips() -> dict:
    return {"tips": NARWHAL_STORE.get_tips()}


@router.delete("/narwhal")
def clear_narwhal(clear_operations: bool = Query(default=False)) -> dict:
    NARWHAL_SERVICE.clear()
    if clear_operations:
        OPERATION_STORE.clear()
    return {
        "status": "cleared",
        "operations_cleared": clear_operations,
    }


@router.post("/swim/bootstrap", response_model=list[SwimMember])
def swim_bootstrap(
    self_address: str | None = Query(default=None),
) -> list[SwimMember]:
    return SWIM_SERVICE.bootstrap(
        self_node_id=CONFIG.node_id,
        self_address=self_address or f"http://node{CONFIG.node_id}:8000",
        peers=CONFIG.peers,
    )


@router.get("/swim/members")
def swim_members() -> dict:
    return {"members": SWIM_STORE.list_members()}


@router.get("/swim/members/{node_id}", response_model=SwimMember)
def swim_member(node_id: int) -> SwimMember:
    try:
        return SWIM_STORE.get_member(node_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/swim/status", response_model=SwimStatus)
def swim_status() -> SwimStatus:
    return SWIM_SERVICE.status(CONFIG.node_id)


@router.post("/swim/ping/{target_node_id}", response_model=SwimProbeResult)
def swim_ping(
    target_node_id: int,
    simulate_success: bool = Query(default=True),
    reason: str | None = Query(default=None),
) -> SwimProbeResult:
    try:
        return SWIM_SERVICE.ping(
            source_node_id=CONFIG.node_id,
            target_node_id=target_node_id,
            simulate_success=simulate_success,
            reason=reason,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/swim/ping-req", response_model=SwimAck)
def swim_ping_req(request: SwimPingReqRequest) -> SwimAck:
    try:
        return SWIM_SERVICE.ping_req(
            source_node_id=CONFIG.node_id,
            intermediary_node_id=request.intermediary_node_id,
            target_node_id=request.target_node_id,
            simulate_success=request.simulate_success,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/swim/probe-demo/{target_node_id}", response_model=SwimProbeResult)
def swim_probe_demo(
    target_node_id: int,
    payload: SwimProbeDemoRequest | None = Body(default=None),
    fail_direct: bool | None = Query(default=None),
    fail_indirect: bool | None = Query(default=None),
) -> SwimProbeResult:
    resolved_fail_direct = (
        fail_direct
        if fail_direct is not None
        else payload.fail_direct
        if payload
        else False
    )
    resolved_fail_indirect = (
        fail_indirect
        if fail_indirect is not None
        else payload.fail_indirect
        if payload
        else False
    )
    try:
        return SWIM_SERVICE.probe_demo(
            target_node_id=target_node_id,
            self_node_id=CONFIG.node_id,
            total_nodes=_node_count(),
            fail_direct=resolved_fail_direct,
            fail_indirect=resolved_fail_indirect,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/swim/gossip", response_model=SwimStatus)
def swim_gossip(envelope: SwimGossipEnvelope) -> SwimStatus:
    if not envelope.updates:
        raise HTTPException(
            status_code=400,
            detail="Gossip update list must not be empty",
        )
    try:
        return SWIM_SERVICE.gossip(
            source_node_id=envelope.source_node_id,
            updates=envelope.updates,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put("/swim/members/{node_id}/alive", response_model=SwimMember)
def swim_mark_alive(node_id: int) -> SwimMember:
    try:
        return SWIM_SERVICE.mark_alive(node_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/swim/members/{node_id}/suspect", response_model=SwimMember)
def swim_mark_suspect(node_id: int) -> SwimMember:
    try:
        return SWIM_SERVICE.suspect(node_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/swim/members/{node_id}/dead", response_model=SwimMember)
def swim_mark_dead(node_id: int) -> SwimMember:
    try:
        return SWIM_SERVICE.mark_dead(node_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/swim/members/{node_id}/recovering", response_model=SwimMember)
def swim_mark_recovering(node_id: int) -> SwimMember:
    try:
        return SWIM_SERVICE.mark_recovering(node_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/swim")
def clear_swim() -> dict:
    SWIM_SERVICE.clear()
    return {"status": "cleared"}


@router.post("/hotstuff/proposals", response_model=HotStuffProposal)
def create_hotstuff_proposal(
    request: HotStuffProposalRequest,
) -> HotStuffProposal:
    try:
        _ensure_consensus_eligible(
            request.proposer_node_id or CONFIG.node_id,
            "proposer",
        )
        return HOTSTUFF_SERVICE.create_proposal_from_batch(
            batch_id=request.batch_id,
            proposer_node_id=request.proposer_node_id or CONFIG.node_id,
            total_nodes=_node_count(),
        )
    except Exception as exc:
        _handle_hotstuff_error(exc)
        raise


@router.get("/hotstuff/proposals")
def list_hotstuff_proposals(limit: int = Query(default=100, ge=0)) -> dict:
    return {
        "proposals": HOTSTUFF_STORE.list_proposals(limit=limit),
        "limit": limit,
    }


@router.get("/hotstuff/proposals/{proposal_id}", response_model=HotStuffProposal)
def get_hotstuff_proposal(proposal_id: str) -> HotStuffProposal:
    try:
        return HOTSTUFF_STORE.get_proposal(proposal_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/hotstuff/proposals/{proposal_id}/vote")
def vote_hotstuff_proposal(
    proposal_id: str,
    payload: HotStuffVoteRequest | None = Body(default=None),
    voter_node_id: int | None = Query(default=None),
    accepted: bool | None = Query(default=None),
    reason: str | None = Query(default=None),
) -> dict:
    resolved_voter = (
        voter_node_id
        if voter_node_id is not None
        else payload.voter_node_id
        if payload and payload.voter_node_id is not None
        else CONFIG.node_id
    )
    resolved_accepted = (
        accepted
        if accepted is not None
        else payload.accepted
        if payload
        else True
    )
    resolved_reason = reason if reason is not None else payload.reason if payload else None
    try:
        _ensure_consensus_eligible(resolved_voter, "voter")
        qc = HOTSTUFF_SERVICE.vote(
            proposal_id=proposal_id,
            voter_node_id=resolved_voter,
            accepted=resolved_accepted,
            reason=resolved_reason,
            total_nodes=_node_count(),
        )
        votes = HOTSTUFF_STORE.get_votes(proposal_id)
    except Exception as exc:
        _handle_hotstuff_error(exc)
        raise
    return {
        "status": "qc_formed" if qc else "vote_recorded",
        "accepted": resolved_accepted,
        "vote_count": len(votes),
        "qc": qc,
    }


@router.post(
    "/hotstuff/proposals/{proposal_id}/form-qc-demo",
    response_model=QuorumCertificate,
)
def form_hotstuff_qc_demo(proposal_id: str) -> QuorumCertificate:
    try:
        return HOTSTUFF_SERVICE.form_qc_demo(
            proposal_id=proposal_id,
            total_nodes=_node_count(),
        )
    except Exception as exc:
        _handle_hotstuff_error(exc)
        raise


@router.get("/hotstuff/proposals/{proposal_id}/votes")
def get_hotstuff_votes(proposal_id: str) -> dict:
    try:
        votes = HOTSTUFF_STORE.get_votes(proposal_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"votes": votes}


@router.get("/hotstuff/qc/{qc_id}", response_model=QuorumCertificate)
def get_hotstuff_qc(qc_id: str) -> QuorumCertificate:
    try:
        return HOTSTUFF_STORE.get_qc(qc_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/hotstuff/qc/{qc_id}/commit", response_model=CommitCertificate)
def commit_hotstuff_qc(qc_id: str) -> CommitCertificate:
    try:
        return HOTSTUFF_SERVICE.commit(qc_id)
    except Exception as exc:
        _handle_hotstuff_error(exc)
        raise


@router.get("/hotstuff/commits")
def list_hotstuff_commits(limit: int = Query(default=100, ge=0)) -> dict:
    return {
        "commits": HOTSTUFF_STORE.list_commits(limit=limit),
        "limit": limit,
    }


@router.get("/hotstuff/status", response_model=HotStuffStatus)
def hotstuff_status(limit: int = Query(default=100, ge=0)) -> HotStuffStatus:
    return HOTSTUFF_SERVICE.status(limit=limit)


@router.post("/hotstuff/view-change-demo", response_model=ViewState)
def hotstuff_view_change_demo(
    payload: HotStuffViewChangeRequest | None = Body(default=None),
    reason: str | None = Query(default=None),
) -> ViewState:
    resolved_reason = reason or (payload.reason if payload else "demo_timeout")
    try:
        return HOTSTUFF_SERVICE.view_change_demo(
            total_nodes=_node_count(),
            reason=resolved_reason,
        )
    except Exception as exc:
        _handle_hotstuff_error(exc)
        raise


@router.delete("/hotstuff")
def clear_hotstuff(
    clear_narwhal: bool = Query(default=False),
    clear_operations: bool = Query(default=False),
) -> dict:
    HOTSTUFF_SERVICE.clear()
    if clear_narwhal:
        NARWHAL_SERVICE.clear()
    if clear_operations:
        OPERATION_STORE.clear()
    return {
        "status": "cleared",
        "narwhal_cleared": clear_narwhal,
        "operations_cleared": clear_operations,
    }


@router.post("/client/submit", response_model=ClientOperation)
def submit_client_operation(input: ClientOperationInput) -> ClientOperation:
    operation = OPERATION_STORE.create(input)
    _append_protocol_event(
        protocol=ProtocolName.HOTSTUFF,
        operation_id=operation.operation_id,
        status=OperationStatus.RECEIVED,
        message="Client operation received by BFT layer",
        details={
            "sender": operation.sender,
            "recipient": operation.recipient,
            "amount": operation.amount,
        },
    )
    return operation


@router.get("/operations")
def list_operations(limit: int = Query(default=100, ge=0)) -> dict:
    return {
        "operations": OPERATION_STORE.list(limit=limit),
        "limit": limit,
    }


@router.get("/operations/{operation_id}", response_model=ClientOperation)
def get_operation(operation_id: str) -> ClientOperation:
    try:
        return OPERATION_STORE.get(operation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/operations/{operation_id}/trace", response_model=OperationTrace)
def get_operation_trace(operation_id: str) -> OperationTrace:
    try:
        return OPERATION_STORE.trace(operation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/operations/{operation_id}/batch", response_model=NarwhalBatchResponse)
def batch_operation(operation_id: str) -> NarwhalBatchResponse:
    try:
        return NARWHAL_SERVICE.create_batch_from_operations(
            author_node_id=CONFIG.node_id,
            total_nodes=_node_count(),
            operation_ids=[operation_id],
            max_operations=1,
        )
    except Exception as exc:
        _handle_narwhal_error(exc)
        raise


@router.post(
    "/operations/{operation_id}/available",
    response_model=BatchCertificate,
)
def mark_operation_available(operation_id: str) -> BatchCertificate:
    batch_id = _find_batch_id_for_operation(operation_id)
    if not batch_id:
        raise HTTPException(
            status_code=409,
            detail="Operation has not been batched by Narwhal yet",
        )
    try:
        certificate = NARWHAL_SERVICE.certify_batch_locally(
            batch_id=batch_id,
            total_nodes=_node_count(),
        )
    except Exception as exc:
        _handle_narwhal_error(exc)
        raise
    if not certificate:
        raise HTTPException(status_code=409, detail="Quorum not reached")
    return certificate


@router.post("/operations/{operation_id}/propose", response_model=HotStuffProposal)
def propose_operation(operation_id: str) -> HotStuffProposal:
    batch = HOTSTUFF_SERVICE.find_batch_by_operation_id(operation_id)
    if not batch:
        raise HTTPException(
            status_code=404,
            detail=f"Batch for operation not found: {operation_id}",
        )
    try:
        return HOTSTUFF_SERVICE.create_proposal_from_batch(
            batch_id=batch.batch_id,
            proposer_node_id=CONFIG.node_id,
            total_nodes=_node_count(),
        )
    except Exception as exc:
        _handle_hotstuff_error(exc)
        raise


@router.post("/operations/{operation_id}/vote")
def vote_operation(
    operation_id: str,
    proposal_id: str | None = Query(default=None),
) -> dict:
    try:
        batch = HOTSTUFF_SERVICE.find_batch_by_operation_id(operation_id)
        if not batch:
            raise HTTPException(
                status_code=404,
                detail=f"Batch for operation not found: {operation_id}",
            )
        proposal = (
            HOTSTUFF_STORE.get_proposal(proposal_id)
            if proposal_id
            else HOTSTUFF_SERVICE.find_latest_proposal_by_batch_id(batch.batch_id)
        )
        if not proposal:
            raise HTTPException(
                status_code=409,
                detail="Operation batch has no HotStuff proposal yet",
            )
        qc = HOTSTUFF_SERVICE.vote(
            proposal_id=proposal.proposal_id,
            voter_node_id=CONFIG.node_id,
            accepted=True,
            reason="operation vote endpoint",
            total_nodes=_node_count(),
        )
        votes = HOTSTUFF_STORE.get_votes(proposal.proposal_id)
    except Exception as exc:
        _handle_hotstuff_error(exc)
        raise
    return {
        "status": "qc_formed" if qc else "vote_recorded",
        "proposal_id": proposal.proposal_id,
        "vote_count": len(votes),
        "qc": qc,
    }


@router.post("/operations/{operation_id}/form-qc", response_model=QuorumCertificate)
def form_quorum_certificate(
    operation_id: str,
    proposal_id: str | None = Query(default=None),
) -> QuorumCertificate:
    try:
        batch = HOTSTUFF_SERVICE.find_batch_by_operation_id(operation_id)
        if not batch:
            raise HTTPException(
                status_code=404,
                detail=f"Batch for operation not found: {operation_id}",
            )
        proposal = (
            HOTSTUFF_STORE.get_proposal(proposal_id)
            if proposal_id
            else HOTSTUFF_SERVICE.find_latest_proposal_by_batch_id(batch.batch_id)
        )
        if not proposal:
            raise HTTPException(
                status_code=409,
                detail="Operation batch has no HotStuff proposal yet",
            )
        return HOTSTUFF_SERVICE.form_qc_demo(
            proposal_id=proposal.proposal_id,
            total_nodes=_node_count(),
        )
    except Exception as exc:
        _handle_hotstuff_error(exc)
        raise


@router.post("/operations/{operation_id}/commit", response_model=CommitCertificate)
def commit_operation(
    operation_id: str,
    proposal_id: str | None = Query(default=None),
) -> CommitCertificate:
    qc = (
        HOTSTUFF_SERVICE.find_qc_by_proposal_id(proposal_id)
        if proposal_id
        else HOTSTUFF_SERVICE.find_qc_by_operation_id(operation_id)
    )
    if not qc:
        raise HTTPException(
            status_code=409,
            detail="Operation has no HotStuff quorum certificate yet",
        )
    try:
        return HOTSTUFF_SERVICE.commit(qc.qc_id)
    except Exception as exc:
        _handle_hotstuff_error(exc)
        raise


@router.post("/operations/{operation_id}/execute", response_model=ClientOperation)
def execute_operation(operation_id: str) -> ClientOperation:
    return _transition_operation(
        operation_id,
        to_status=OperationStatus.EXECUTED,
        protocol=ProtocolName.HOTSTUFF,
        message="Operation executed by demo state machine boundary",
        details={
            "execution": (
                "Logical/demo execution only; integration with VetClinic domain "
                "and blockchain execution is planned for a later stage."
            )
        },
    )


@router.post("/operations/{operation_id}/run-demo", response_model=OperationTrace)
def run_demo_flow(operation_id: str) -> OperationTrace:
    try:
        operation = OPERATION_STORE.get(operation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        if operation.status == OperationStatus.RECEIVED:
            batch_response = NARWHAL_SERVICE.create_batch_from_operations(
                author_node_id=CONFIG.node_id,
                total_nodes=_node_count(),
                operation_ids=[operation_id],
                max_operations=1,
            )
            batch_id = batch_response.batch.batch_id
        else:
            batch = HOTSTUFF_SERVICE.find_batch_by_operation_id(operation_id)
            if not batch and operation.status in {
                OperationStatus.BATCHED,
                OperationStatus.AVAILABLE,
                OperationStatus.PROPOSED,
                OperationStatus.VOTED,
                OperationStatus.QC_FORMED,
                OperationStatus.COMMITTED,
            }:
                raise HTTPException(
                    status_code=409,
                    detail="Operation has no Narwhal batch context",
                )
            batch_id = batch.batch_id if batch else None

        operation = OPERATION_STORE.get(operation_id)
        if operation.status == OperationStatus.BATCHED and batch_id:
            certificate = NARWHAL_SERVICE.certify_batch_locally(
                batch_id=batch_id,
                total_nodes=_node_count(),
            )
            if not certificate:
                raise HTTPException(status_code=409, detail="Narwhal quorum not reached")

        operation = OPERATION_STORE.get(operation_id)
        if operation.status == OperationStatus.AVAILABLE:
            HOTSTUFF_SERVICE.run_hotstuff_demo_for_operation(
                operation_id=operation_id,
                proposer_node_id=CONFIG.node_id,
                total_nodes=_node_count(),
            )

        operation = OPERATION_STORE.get(operation_id)
        if operation.status == OperationStatus.COMMITTED:
            _transition_operation(
                operation_id,
                to_status=OperationStatus.EXECUTED,
                protocol=ProtocolName.HOTSTUFF,
                message="Operation executed by demo state machine boundary",
                details={
                    "execution": (
                        "Logical/demo execution only; integration with VetClinic domain "
                        "and blockchain execution is planned for a later stage."
                    )
                },
            )
        return OPERATION_STORE.trace(operation_id)
    except HTTPException as exc:
        if exc.status_code == 409:
            try:
                _transition_operation(
                    operation_id,
                    to_status=OperationStatus.FAILED,
                    protocol=ProtocolName.HOTSTUFF,
                    message="Demo BFT flow failed",
                    details={"reason": exc.detail},
                )
            except HTTPException:
                pass
        raise


@router.delete("/operations")
def clear_operations() -> dict:
    OPERATION_STORE.clear()
    EVENT_LOG.clear()
    return {"status": "cleared"}
