from __future__ import annotations

import pytest


@pytest.mark.bft
@pytest.mark.contract
def test_fault_injection_router_contract(bft_client):
    created = bft_client.post(
        "/bft/faults/rules",
        json={
            "fault_type": "DROP",
            "protocol": "HOTSTUFF",
            "message_kind": "VOTE",
            "probability": 1.0,
        },
    )
    assert created.status_code == 200
    rule_id = created.json()["rule_id"]
    assert bft_client.get("/bft/faults/rules").status_code == 200
    assert bft_client.put(f"/bft/faults/rules/{rule_id}/disable").status_code == 200
    assert bft_client.put(f"/bft/faults/rules/{rule_id}/enable").status_code == 200

    partition = bft_client.post(
        "/bft/faults/partitions",
        json={"groups": [[1, 2], [3, 4]]},
    )
    assert partition.status_code == 200
    assert bft_client.get("/bft/faults/status").status_code == 200
    decision = bft_client.post(
        "/bft/faults/evaluate",
        json={
            "protocol": "HOTSTUFF",
            "message_kind": "VOTE",
            "source_node_id": 1,
            "target_node_id": 3,
            "message_id": "vote-1",
        },
    )
    assert decision.status_code == 200
    assert decision.json()["should_drop"] is True
    assert bft_client.get("/bft/faults/injected").status_code == 200
    assert bft_client.delete("/bft/faults").status_code == 200
