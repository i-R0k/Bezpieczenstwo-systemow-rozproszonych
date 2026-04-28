from __future__ import annotations

import uuid
from datetime import datetime, timezone

from vetclinic_api.bft.common.operations import ClientOperationInput
from vetclinic_api.bft.common.types import (
    FaultType,
    MessageKind,
    NodeStatus,
    OperationStatus,
    ProtocolName,
)
from vetclinic_api.bft.crypto.envelope import BftMessagePayload
from vetclinic_api.bft.observability.health import HealthService
from vetclinic_api.bft.observability.report import BftDemoReport, BftDemoStep, build_step


class BftDemoScenarioRunner:
    def __init__(
        self,
        *,
        operation_store,
        narwhal_service,
        hotstuff_service,
        swim_service,
        fault_service,
        checkpoint_service,
        recovery_service,
        crypto_service,
        event_log,
        metrics,
        health_service: HealthService,
    ) -> None:
        self.operation_store = operation_store
        self.narwhal_service = narwhal_service
        self.hotstuff_service = hotstuff_service
        self.swim_service = swim_service
        self.fault_service = fault_service
        self.checkpoint_service = checkpoint_service
        self.recovery_service = recovery_service
        self.crypto_service = crypto_service
        self.event_log = event_log
        self.metrics = metrics
        self.health_service = health_service

    def run_full_demo(self, total_nodes: int = 6) -> BftDemoReport:
        started = datetime.now(timezone.utc)
        steps: list[BftDemoStep] = []
        errors: list[str] = []
        operation_id: str | None = None
        checkpoint_id: str | None = None
        recovered_node_id: int | None = None
        try:
            step_started = datetime.now(timezone.utc)
            self.crypto_service.ensure_demo_keys(total_nodes)
            peers = [f"http://node{node_id}:8000" for node_id in range(2, total_nodes + 1)]
            self.swim_service.bootstrap(1, "http://node1:8000", peers)
            health_before = self.health_service.check_all()
            steps.append(build_step("Bootstrap", "ok", step_started, {"health": health_before.model_dump(mode="json")}))

            step_started = datetime.now(timezone.utc)
            operation = self.operation_store.create(
                ClientOperationInput(sender="demo", recipient="state-machine", amount=1.0, payload={"demo": True})
            )
            operation_id = operation.operation_id
            steps.append(build_step("Submit operation", "ok", step_started, {"operation_id": operation_id, "status": operation.status.value}))

            step_started = datetime.now(timezone.utc)
            batch_response = self.narwhal_service.create_batch_from_operations(1, total_nodes, [operation_id], 1)
            certificate = self.narwhal_service.certify_batch_locally(batch_response.batch.batch_id, total_nodes)
            steps.append(build_step("Narwhal", "ok", step_started, {"batch_id": batch_response.batch.batch_id, "certificate": certificate.model_dump(mode="json") if certificate else None}))

            step_started = datetime.now(timezone.utc)
            proposal = self.hotstuff_service.create_proposal_from_batch(batch_response.batch.batch_id, 1, total_nodes)
            qc = self.hotstuff_service.form_qc_demo(proposal.proposal_id, total_nodes)
            commit = self.hotstuff_service.commit(qc.qc_id)
            steps.append(build_step("HotStuff", "ok", step_started, {"proposal_id": proposal.proposal_id, "qc_id": qc.qc_id, "commit_id": commit.commit_id}))

            step_started = datetime.now(timezone.utc)
            executed = self.operation_store.transition(
                operation_id,
                OperationStatus.EXECUTED,
                ProtocolName.HOTSTUFF,
                "Operation executed by final demo scenario",
            )
            steps.append(build_step("Execute", "ok", step_started, {"status": executed.status.value}))

            step_started = datetime.now(timezone.utc)
            rule = self.fault_service.create_rule(
                fault_type=FaultType.DROP,
                protocol=ProtocolName.SWIM,
                message_kind=MessageKind.SWIM_PING,
            )
            probe = self.swim_service.ping(1, 2)
            self.fault_service.fault_store.disable_rule(rule.rule_id)
            steps.append(build_step("Fault injection", "ok", step_started, {"rule_id": rule.rule_id, "probe_status": probe.status_after.value}))

            step_started = datetime.now(timezone.utc)
            snapshot = self.checkpoint_service.create_snapshot(1)
            checkpoint = self.checkpoint_service.certify_snapshot(snapshot.snapshot_id, total_nodes)
            checkpoint_id = checkpoint.checkpoint_id
            steps.append(build_step("Checkpoint", "ok", step_started, {"snapshot_id": snapshot.snapshot_id, "checkpoint_id": checkpoint_id, "state_hash": snapshot.state_hash}))

            step_started = datetime.now(timezone.utc)
            self.swim_service.mark_recovering(3)
            result = self.recovery_service.recover_node(3, checkpoint_id, reason="demo_state_corruption")
            recovered_node_id = result.node_id
            steps.append(build_step("Recovery", "ok", step_started, {"node_id": result.node_id, "status": result.status, "hash": result.applied_state_hash}))

            step_started = datetime.now(timezone.utc)
            signed = self.crypto_service.sign_message(
                BftMessagePayload(
                    protocol=ProtocolName.HOTSTUFF,
                    message_kind=MessageKind.VOTE,
                    source_node_id=1,
                    body={"demo": "crypto"},
                ),
                1,
            )
            verified = self.crypto_service.verify_message(signed)
            replay = self.crypto_service.verify_message(signed)
            steps.append(build_step("Crypto verification", "ok", step_started, {"valid": verified.valid, "replay": replay.replay}))

            step_started = datetime.now(timezone.utc)
            health_after = self.health_service.check_all()
            metrics_snapshot = self.metrics.snapshot()
            steps.append(build_step("Health after", "ok", step_started, {"health": health_after.model_dump(mode="json")}))
            status = "ok" if not errors else "error"
        except Exception as exc:
            errors.append(str(exc))
            metrics_snapshot = self.metrics.snapshot()
            status = "error"

        final_status = None
        if operation_id:
            final_status = self.operation_store.get(operation_id).status.value
        return BftDemoReport(
            report_id=str(uuid.uuid4()),
            status=status,
            started_at=started,
            finished_at=datetime.now(timezone.utc),
            steps=steps,
            operation_id=operation_id,
            final_operation_status=final_status,
            checkpoint_id=checkpoint_id,
            recovered_node_id=recovered_node_id,
            metrics_snapshot=metrics_snapshot,
            errors=errors,
        )
