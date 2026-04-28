from __future__ import annotations

import pytest
from pydantic import ValidationError

from vetclinic_api.bft.common.types import FaultType, MessageKind, ProtocolName
from vetclinic_api.bft.fault_injection.models import InjectedFault


@pytest.mark.bft
@pytest.mark.contract
def test_fault_rule_lifecycle_and_validation(fault_store):
    rule = fault_store.create_rule(
        fault_type=FaultType.DROP,
        protocol=ProtocolName.NARWHAL,
        message_kind=MessageKind.BATCH,
    )
    assert rule.rule_id
    assert fault_store.get_rule(rule.rule_id) == rule
    assert fault_store.disable_rule(rule.rule_id).enabled is False
    assert fault_store.enable_rule(rule.rule_id).enabled is True
    fault_store.delete_rule(rule.rule_id)
    with pytest.raises(KeyError):
        fault_store.get_rule(rule.rule_id)
    with pytest.raises(ValidationError):
        fault_store.create_rule(fault_type=FaultType.DROP, probability=1.1)
    with pytest.raises(ValidationError):
        fault_store.create_rule(fault_type=FaultType.DELAY, delay_ms=-1)


@pytest.mark.bft
@pytest.mark.contract
def test_fault_partition_fault_counters_and_clear(fault_store):
    partition = fault_store.create_partition([[1, 2], [3]])
    assert partition.partition_id
    assert fault_store.disable_partition(partition.partition_id).enabled is False
    assert fault_store.enable_partition(partition.partition_id).enabled is True
    with pytest.raises(ValueError):
        fault_store.create_partition([[1, 2], [2, 3]])

    fault_store.record_fault(
        InjectedFault(
            fault_id="fault-1",
            rule_id="rule-1",
            fault_type=FaultType.DROP,
            protocol=ProtocolName.HOTSTUFF,
            message_kind=MessageKind.VOTE,
            applied=True,
            reason="test",
        )
    )
    assert fault_store.counters()["DROP"] == 1
    fault_store.clear()
    assert fault_store.list_rules() == []
    assert fault_store.list_partitions() == []
    assert fault_store.list_injected_faults() == []
