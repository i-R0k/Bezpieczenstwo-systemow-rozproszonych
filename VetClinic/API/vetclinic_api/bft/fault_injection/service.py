from __future__ import annotations

import random
import uuid

from vetclinic_api.bft.common.events import EventLog, ProtocolEvent
from vetclinic_api.bft.common.types import FaultType
from vetclinic_api.bft.fault_injection.models import (
    FaultDecision,
    FaultEvaluationContext,
    FaultInjectionStatus,
    FaultRule,
    InjectedFault,
    NetworkPartition,
)
from vetclinic_api.bft.fault_injection.store import InMemoryFaultInjectionStore


class FaultInjectionService:
    def __init__(
        self,
        fault_store: InMemoryFaultInjectionStore,
        event_log: EventLog,
    ) -> None:
        self.fault_store = fault_store
        self.event_log = event_log

    def evaluate(self, context: FaultEvaluationContext) -> FaultDecision:
        decision = FaultDecision()
        if self.is_partition_blocked(context.source_node_id, context.target_node_id):
            fault = self._record_fault(
                rule_id="network-partition",
                fault_type=FaultType.NETWORK_PARTITION,
                context=context,
                reason="blocked_by_partition",
                metadata={"partition": True},
            )
            decision.blocked_by_partition = True
            decision.should_drop = True
            decision.injected_faults.append(fault)

        for rule in self.fault_store.list_rules():
            if not rule.enabled or not self._rule_matches(rule, context):
                continue
            if not self.should_apply_probability(rule.probability):
                continue
            fault = self._record_fault(
                rule_id=rule.rule_id,
                fault_type=rule.fault_type,
                context=context,
                reason="rule_applied",
                metadata=rule.metadata,
            )
            decision.injected_faults.append(fault)
            if rule.fault_type == FaultType.DROP:
                decision.should_drop = True
            elif rule.fault_type == FaultType.DELAY:
                decision.should_delay = True
                decision.delay_ms = max(decision.delay_ms, rule.delay_ms or 0)
            elif rule.fault_type == FaultType.DUPLICATE:
                decision.should_duplicate = True
            elif rule.fault_type == FaultType.REPLAY:
                decision.should_replay = True
            elif rule.fault_type == FaultType.EQUIVOCATION:
                decision.should_equivocate = True
            elif rule.fault_type == FaultType.NETWORK_PARTITION:
                decision.blocked_by_partition = True
                decision.should_drop = True
            elif rule.fault_type == FaultType.LEADER_FAILURE:
                decision.leader_failed = True
            elif rule.fault_type == FaultType.STATE_CORRUPTION:
                # Placeholder until checkpointing/state transfer are introduced.
                pass
        return decision

    def create_rule(self, **kwargs) -> FaultRule:
        return self.fault_store.create_rule(**kwargs)

    def create_partition(self, groups: list[list[int]]) -> NetworkPartition:
        return self.fault_store.create_partition(groups)

    def clear(self) -> None:
        self.fault_store.clear()

    def status(self) -> FaultInjectionStatus:
        return self.fault_store.status()

    def is_partition_blocked(
        self,
        source_node_id: int | None,
        target_node_id: int | None,
    ) -> bool:
        if source_node_id is None or target_node_id is None:
            return False
        for partition in self.fault_store.list_partitions():
            if not partition.enabled:
                continue
            source_group = self._find_group(partition, source_node_id)
            target_group = self._find_group(partition, target_node_id)
            if source_group is not None and target_group is not None:
                return source_group != target_group
        return False

    def should_apply_probability(self, probability: float) -> bool:
        if probability < 0.0 or probability > 1.0:
            raise ValueError("probability must be between 0.0 and 1.0")
        if probability == 0.0:
            return False
        if probability == 1.0:
            return True
        return random.random() <= probability

    @staticmethod
    def _find_group(partition: NetworkPartition, node_id: int) -> int | None:
        for index, group in enumerate(partition.groups):
            if node_id in group:
                return index
        return None

    @staticmethod
    def _rule_matches(rule: FaultRule, context: FaultEvaluationContext) -> bool:
        return (
            (rule.protocol is None or rule.protocol == context.protocol)
            and (
                rule.source_node_id is None
                or rule.source_node_id == context.source_node_id
            )
            and (
                rule.target_node_id is None
                or rule.target_node_id == context.target_node_id
            )
            and (
                rule.message_kind is None
                or rule.message_kind == context.message_kind
            )
        )

    def _record_fault(
        self,
        *,
        rule_id: str,
        fault_type: FaultType,
        context: FaultEvaluationContext,
        reason: str,
        metadata: dict,
    ) -> InjectedFault:
        fault = InjectedFault(
            fault_id=str(uuid.uuid4()),
            rule_id=rule_id,
            fault_type=fault_type,
            protocol=context.protocol,
            source_node_id=context.source_node_id,
            target_node_id=context.target_node_id,
            message_kind=context.message_kind,
            operation_id=context.operation_id,
            message_id=context.message_id,
            applied=True,
            reason=reason,
            metadata={**context.metadata, **metadata},
        )
        self.fault_store.record_fault(fault)
        self.event_log.append(
            ProtocolEvent(
                event_id=str(uuid.uuid4()),
                node_id=context.source_node_id,
                protocol=context.protocol,
                operation_id=context.operation_id,
                status=None,
                message="fault_injected",
                details={
                    "fault_id": fault.fault_id,
                    "rule_id": rule_id,
                    "fault_type": fault_type.value,
                    "message_kind": context.message_kind.value,
                    "message_id": context.message_id,
                    "reason": reason,
                },
            )
        )
        return fault
