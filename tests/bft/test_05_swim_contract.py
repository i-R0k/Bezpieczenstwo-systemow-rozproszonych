from __future__ import annotations

import pytest

from vetclinic_api.bft.common.events import EventLog
from vetclinic_api.bft.common.operations import ClientOperationInput, InMemoryOperationStore
from vetclinic_api.bft.common.types import NodeStatus
from vetclinic_api.bft.hotstuff.service import HotStuffService
from vetclinic_api.bft.hotstuff.store import InMemoryHotStuffStore
from vetclinic_api.bft.narwhal.service import NarwhalService
from vetclinic_api.bft.narwhal.store import InMemoryNarwhalStore
from vetclinic_api.bft.swim.models import SwimGossipUpdate
from vetclinic_api.bft.swim.service import SwimService, is_node_eligible_for_consensus


def _bootstrap(service):
    return service.bootstrap(1, "http://node1:8000", ["http://node2:8000", "http://node3:8000"])


@pytest.mark.bft
@pytest.mark.contract
def test_swim_bootstrap_and_status(swim_store, event_log):
    service = SwimService(swim_store, event_log)
    members = _bootstrap(service)
    assert {m.node_id for m in members} == {1, 2, 3}
    assert all(m.status == NodeStatus.ALIVE for m in members)
    status = service.status(1)
    assert status.alive == 3
    assert status.suspect == status.dead == status.recovering == 0


@pytest.mark.bft
@pytest.mark.contract
def test_swim_ping_pingreq_and_events(swim_store, event_log):
    service = SwimService(swim_store, event_log)
    _bootstrap(service)
    ok = service.ping(1, 2, simulate_success=True)
    assert ok.ack and ok.ack.accepted is True
    missed = service.ping(1, 2, simulate_success=False)
    assert missed.status_after == NodeStatus.SUSPECT
    second = service.ping(1, 2, simulate_success=False)
    assert second.status_after == NodeStatus.DEAD
    assert service.ping_req(1, 3, 2, simulate_success=True).accepted is True
    assert service.ping_req(1, 3, 2, simulate_success=False).accepted is False
    messages = {event.message for event in event_log.list()}
    assert {"swim_ping_ack", "swim_ping_missed", "swim_ping_req"} <= messages


@pytest.mark.bft
@pytest.mark.contract
def test_swim_probe_demo(swim_store, event_log):
    service = SwimService(swim_store, event_log)
    _bootstrap(service)
    assert service.probe_demo(2, 1, 3).status_after == NodeStatus.ALIVE
    assert service.probe_demo(2, 1, 3, fail_direct=True).status_after == NodeStatus.ALIVE
    result = service.probe_demo(2, 1, 3, fail_direct=True, fail_indirect=True)
    assert result.status_after in {NodeStatus.SUSPECT, NodeStatus.DEAD}


@pytest.mark.bft
@pytest.mark.contract
def test_swim_gossip_and_recovery(swim_store, event_log):
    service = SwimService(swim_store, event_log)
    _bootstrap(service)
    swim_store.upsert_member(2, "http://node2:8000", NodeStatus.ALIVE, incarnation=3)
    service.gossip(1, [SwimGossipUpdate(node_id=2, status=NodeStatus.DEAD, incarnation=2, observed_by=1)])
    assert swim_store.get_member(2).status == NodeStatus.ALIVE
    service.gossip(1, [SwimGossipUpdate(node_id=2, status=NodeStatus.SUSPECT, incarnation=4, observed_by=1)])
    assert swim_store.get_member(2).status == NodeStatus.SUSPECT
    service.gossip(1, [SwimGossipUpdate(node_id=2, status=NodeStatus.DEAD, incarnation=4, observed_by=1)])
    assert swim_store.get_member(2).status == NodeStatus.DEAD
    incarnation = swim_store.get_member(2).incarnation
    service.mark_alive(2)
    assert swim_store.get_member(2).incarnation == incarnation + 1
    service.mark_recovering(2)
    assert swim_store.get_member(2).status == NodeStatus.RECOVERING
    assert is_node_eligible_for_consensus(swim_store, 2) is False


@pytest.mark.bft
@pytest.mark.integration
def test_swim_hotstuff_integration(swim_store, event_log):
    swim = SwimService(swim_store, event_log)
    _bootstrap(swim)
    operation_store = InMemoryOperationStore()
    narwhal_store = InMemoryNarwhalStore(total_nodes=3)
    hotstuff_store = InMemoryHotStuffStore(total_nodes=3)
    narwhal = NarwhalService(operation_store, event_log, narwhal_store)
    hotstuff = HotStuffService(operation_store, event_log, narwhal_store, hotstuff_store, swim_store)
    op = operation_store.create(ClientOperationInput(sender="a", recipient="b", amount=1))
    batch = narwhal.create_batch_from_operations(1, 3, [op.operation_id], 1).batch
    narwhal.certify_batch_locally(batch.batch_id, 3)
    swim.mark_dead(2)
    with pytest.raises(ValueError):
        hotstuff.create_proposal_from_batch(batch.batch_id, 2, 3)
    proposal = hotstuff.create_proposal_from_batch(batch.batch_id, 1, 3)
    with pytest.raises(ValueError):
        hotstuff.vote(proposal.proposal_id, 2, total_nodes=3)
    qc = hotstuff.vote(proposal.proposal_id, 1, total_nodes=3)
    assert qc is None or qc.valid is True


@pytest.mark.bft
@pytest.mark.contract
def test_swim_router_contract(bft_client):
    assert bft_client.post("/bft/swim/bootstrap").status_code == 200
    assert bft_client.get("/bft/swim/status").status_code == 200
    assert bft_client.post("/bft/swim/ping/2?simulate_success=false").status_code == 200
    assert bft_client.put("/bft/swim/members/2/dead").status_code == 200
    assert bft_client.put("/bft/swim/members/2/alive").status_code == 200
    payload = {
        "source_node_id": 1,
        "updates": [
            {
                "node_id": 2,
                "status": "DEAD",
                "incarnation": 3,
                "observed_by": 1,
            }
        ],
    }
    assert bft_client.post("/bft/swim/gossip", json=payload).status_code == 200
