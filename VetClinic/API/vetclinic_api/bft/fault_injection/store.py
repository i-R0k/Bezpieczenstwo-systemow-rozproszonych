from __future__ import annotations

import threading
import uuid
from collections import Counter

from vetclinic_api.bft.common.types import FaultType, MessageKind, ProtocolName
from vetclinic_api.bft.fault_injection.models import (
    FaultInjectionStatus,
    FaultRule,
    InjectedFault,
    NetworkPartition,
)


class InMemoryFaultInjectionStore:
    def __init__(self) -> None:
        self._rules: dict[str, FaultRule] = {}
        self._partitions: dict[str, NetworkPartition] = {}
        self._faults: list[InjectedFault] = []
        self._lock = threading.Lock()

    def add_rule(self, rule: FaultRule) -> FaultRule:
        self._validate_rule(rule)
        with self._lock:
            self._rules[rule.rule_id] = rule
            return rule

    def create_rule(
        self,
        *,
        fault_type: FaultType,
        protocol: ProtocolName | None = None,
        source_node_id: int | None = None,
        target_node_id: int | None = None,
        message_kind: MessageKind | None = None,
        enabled: bool = True,
        probability: float = 1.0,
        delay_ms: int | None = None,
        partition_id: str | None = None,
        metadata: dict | None = None,
    ) -> FaultRule:
        rule = FaultRule(
            rule_id=str(uuid.uuid4()),
            fault_type=fault_type,
            protocol=protocol,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            message_kind=message_kind,
            enabled=enabled,
            probability=probability,
            delay_ms=delay_ms,
            partition_id=partition_id,
            metadata=metadata or {},
        )
        return self.add_rule(rule)

    def get_rule(self, rule_id: str) -> FaultRule:
        with self._lock:
            try:
                return self._rules[rule_id]
            except KeyError as exc:
                raise KeyError(f"Fault rule not found: {rule_id}") from exc

    def list_rules(self) -> list[FaultRule]:
        with self._lock:
            return list(self._rules.values())

    def enable_rule(self, rule_id: str) -> FaultRule:
        return self._set_rule_enabled(rule_id, True)

    def disable_rule(self, rule_id: str) -> FaultRule:
        return self._set_rule_enabled(rule_id, False)

    def delete_rule(self, rule_id: str) -> None:
        with self._lock:
            if rule_id not in self._rules:
                raise KeyError(f"Fault rule not found: {rule_id}")
            del self._rules[rule_id]

    def add_partition(self, partition: NetworkPartition) -> NetworkPartition:
        self._validate_partition_groups(partition.groups)
        with self._lock:
            self._partitions[partition.partition_id] = partition
            return partition

    def create_partition(self, groups: list[list[int]]) -> NetworkPartition:
        partition = NetworkPartition(
            partition_id=str(uuid.uuid4()),
            groups=groups,
        )
        return self.add_partition(partition)

    def get_partition(self, partition_id: str) -> NetworkPartition:
        with self._lock:
            try:
                return self._partitions[partition_id]
            except KeyError as exc:
                raise KeyError(f"Network partition not found: {partition_id}") from exc

    def list_partitions(self) -> list[NetworkPartition]:
        with self._lock:
            return list(self._partitions.values())

    def enable_partition(self, partition_id: str) -> NetworkPartition:
        return self._set_partition_enabled(partition_id, True)

    def disable_partition(self, partition_id: str) -> NetworkPartition:
        return self._set_partition_enabled(partition_id, False)

    def delete_partition(self, partition_id: str) -> None:
        with self._lock:
            if partition_id not in self._partitions:
                raise KeyError(f"Network partition not found: {partition_id}")
            del self._partitions[partition_id]

    def record_fault(self, fault: InjectedFault) -> InjectedFault:
        with self._lock:
            self._faults.append(fault)
            return fault

    def list_injected_faults(self, limit: int = 100) -> list[InjectedFault]:
        if limit < 0:
            raise ValueError("limit must be greater than or equal to 0")
        with self._lock:
            if limit == 0:
                return []
            return list(self._faults[-limit:])

    def counters(self) -> dict[str, int]:
        with self._lock:
            counter = Counter(fault.fault_type.name for fault in self._faults)
            return dict(counter)

    def status(self) -> FaultInjectionStatus:
        return FaultInjectionStatus(
            rules=self.list_rules(),
            partitions=self.list_partitions(),
            injected_faults=self.list_injected_faults(),
            counters=self.counters(),
        )

    def clear(self) -> None:
        with self._lock:
            self._rules.clear()
            self._partitions.clear()
            self._faults.clear()

    def _set_rule_enabled(self, rule_id: str, enabled: bool) -> FaultRule:
        with self._lock:
            if rule_id not in self._rules:
                raise KeyError(f"Fault rule not found: {rule_id}")
            rule = self._rules[rule_id].model_copy(update={"enabled": enabled})
            self._rules[rule_id] = rule
            return rule

    def _set_partition_enabled(
        self,
        partition_id: str,
        enabled: bool,
    ) -> NetworkPartition:
        with self._lock:
            if partition_id not in self._partitions:
                raise KeyError(f"Network partition not found: {partition_id}")
            partition = self._partitions[partition_id].model_copy(
                update={"enabled": enabled}
            )
            self._partitions[partition_id] = partition
            return partition

    @staticmethod
    def _validate_rule(rule: FaultRule) -> None:
        if rule.probability < 0.0 or rule.probability > 1.0:
            raise ValueError("probability must be between 0.0 and 1.0")
        if rule.delay_ms is not None and rule.delay_ms < 0:
            raise ValueError("delay_ms must be greater than or equal to 0")

    @staticmethod
    def _validate_partition_groups(groups: list[list[int]]) -> None:
        if not groups:
            raise ValueError("partition groups must not be empty")
        seen: set[int] = set()
        for group in groups:
            if not group:
                raise ValueError("partition groups must not contain empty groups")
            for node_id in group:
                if node_id in seen:
                    raise ValueError(
                        f"node {node_id} appears in more than one partition group"
                    )
                seen.add(node_id)


FAULT_STORE = InMemoryFaultInjectionStore()
