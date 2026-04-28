from __future__ import annotations

from typing import Any

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

from vetclinic_api.bft.common.events import ProtocolEvent


COUNTER_NAMES = [
    "bft_operations_submitted_total",
    "bft_operations_executed_total",
    "bft_narwhal_batches_created_total",
    "bft_narwhal_batch_certificates_total",
    "bft_hotstuff_proposals_total",
    "bft_hotstuff_votes_total",
    "bft_hotstuff_qc_total",
    "bft_hotstuff_commits_total",
    "bft_hotstuff_view_changes_total",
    "bft_swim_ping_total",
    "bft_swim_suspect_total",
    "bft_swim_dead_total",
    "bft_faults_injected_total",
    "bft_replay_detected_total",
    "bft_equivocation_detected_total",
    "bft_checkpoints_created_total",
    "bft_recoveries_completed_total",
    "bft_crypto_messages_signed_total",
    "bft_crypto_messages_verified_total",
    "bft_crypto_messages_rejected_total",
]

GAUGE_NAMES = [
    "bft_operation_store_size",
    "bft_narwhal_dag_vertices",
    "bft_hotstuff_current_view",
    "bft_hotstuff_committed_blocks",
    "bft_swim_alive_nodes",
    "bft_swim_suspect_nodes",
    "bft_swim_dead_nodes",
    "bft_swim_recovering_nodes",
    "bft_fault_rules_enabled",
    "bft_checkpoints_total",
    "bft_recovery_states_total",
    "bft_crypto_registered_public_keys",
]

HISTOGRAM_NAMES = [
    "bft_operation_end_to_end_seconds",
    "bft_checkpoint_creation_seconds",
    "bft_recovery_duration_seconds",
]

EVENT_COUNTER_MAP = {
    "Client operation received by BFT layer": "bft_operations_submitted_total",
    "Operation executed by demo state machine boundary": "bft_operations_executed_total",
    "batch_created": "bft_narwhal_batches_created_total",
    "batch_certified": "bft_narwhal_batch_certificates_total",
    "hotstuff_proposal_created": "bft_hotstuff_proposals_total",
    "hotstuff_vote_recorded": "bft_hotstuff_votes_total",
    "hotstuff_qc_formed": "bft_hotstuff_qc_total",
    "hotstuff_block_committed": "bft_hotstuff_commits_total",
    "hotstuff_view_changed": "bft_hotstuff_view_changes_total",
    "swim_ping_ack": "bft_swim_ping_total",
    "swim_ping_missed": "bft_swim_ping_total",
    "swim_member_suspect": "bft_swim_suspect_total",
    "swim_member_dead": "bft_swim_dead_total",
    "fault_injected": "bft_faults_injected_total",
    "checkpoint_snapshot_created": "bft_checkpoints_created_total",
    "checkpoint_created": "bft_checkpoints_created_total",
    "state_transfer_applied": "bft_recoveries_completed_total",
    "bft_message_signed": "bft_crypto_messages_signed_total",
    "bft_message_verified": "bft_crypto_messages_verified_total",
    "bft_message_rejected": "bft_crypto_messages_rejected_total",
}


class BftMetrics:
    def __init__(self) -> None:
        self._build_registry()

    def _build_registry(self) -> None:
        self.registry = CollectorRegistry()
        self.counters = {
            name: Counter(name, name.replace("_", " "), registry=self.registry)
            for name in COUNTER_NAMES
        }
        self.gauges = {
            name: Gauge(name, name.replace("_", " "), registry=self.registry)
            for name in GAUGE_NAMES
        }
        self.histograms = {
            name: Histogram(name, name.replace("_", " "), registry=self.registry)
            for name in HISTOGRAM_NAMES
        }

    def record_event(self, event: ProtocolEvent) -> None:
        counter_name = EVENT_COUNTER_MAP.get(event.message)
        if counter_name:
            self.counters[counter_name].inc()
        if event.message == "fault_injected":
            fault_type = str(event.details.get("fault_type", ""))
            if fault_type == "REPLAY":
                self.counters["bft_replay_detected_total"].inc()
            if fault_type == "EQUIVOCATION":
                self.counters["bft_equivocation_detected_total"].inc()
        if event.message == "bft_message_rejected" and event.details.get("reason") == "replay_detected":
            self.counters["bft_replay_detected_total"].inc()

    def refresh_gauges(
        self,
        *,
        operation_store=None,
        narwhal_store=None,
        hotstuff_store=None,
        swim_store=None,
        fault_store=None,
        checkpoint_store=None,
        recovery_store=None,
        node_key_registry=None,
        self_node_id: int = 1,
    ) -> dict[str, float]:
        values: dict[str, float] = {}
        if operation_store is not None:
            values["bft_operation_store_size"] = float(len(operation_store.list(limit=10000)))
        if narwhal_store is not None:
            values["bft_narwhal_dag_vertices"] = float(narwhal_store.get_dag().total_batches)
        if hotstuff_store is not None:
            values["bft_hotstuff_current_view"] = float(hotstuff_store.current_view().view)
            values["bft_hotstuff_committed_blocks"] = float(len(hotstuff_store.list_commits(limit=10000)))
        if swim_store is not None:
            status = swim_store.status(self_node_id)
            values["bft_swim_alive_nodes"] = float(status.alive)
            values["bft_swim_suspect_nodes"] = float(status.suspect)
            values["bft_swim_dead_nodes"] = float(status.dead)
            values["bft_swim_recovering_nodes"] = float(status.recovering)
        if fault_store is not None:
            values["bft_fault_rules_enabled"] = float(sum(1 for rule in fault_store.list_rules() if rule.enabled))
        if checkpoint_store is not None:
            values["bft_checkpoints_total"] = float(len(checkpoint_store.list_certificates(limit=10000)))
        if recovery_store is not None:
            values["bft_recovery_states_total"] = float(len(recovery_store.status().recovered_nodes))
        if node_key_registry is not None:
            values["bft_crypto_registered_public_keys"] = float(len(node_key_registry.public_keys()))
        for name, value in values.items():
            self.gauges[name].set(value)
        return values

    def snapshot(self) -> dict[str, Any]:
        counters = {
            name: metric._value.get()  # prometheus-client exposes this for tests.
            for name, metric in self.counters.items()
        }
        gauges = {
            name: metric._value.get()
            for name, metric in self.gauges.items()
        }
        return {"counters": counters, "gauges": gauges}

    def export_latest_text(self) -> str:
        return generate_latest(self.registry).decode("utf-8")

    def reset_for_tests(self) -> None:
        self._build_registry()


BFT_METRICS = BftMetrics()
