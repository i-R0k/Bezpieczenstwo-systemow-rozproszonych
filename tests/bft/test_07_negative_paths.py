from __future__ import annotations

import pytest

from vetclinic_api.bft.common.types import OperationStatus, ProtocolName


@pytest.mark.bft
@pytest.mark.contract
def test_negative_router_paths(bft_client, operation_store, sample_operation_input):
    assert bft_client.get("/bft/operations/missing").status_code == 404
    assert bft_client.post("/bft/operations/missing/batch").status_code in {404, 409}
    assert bft_client.post("/bft/narwhal/batches/missing/certify-demo").status_code == 404

    operation = bft_client.post(
        "/bft/client/submit",
        json={"sender": "alice", "recipient": "bob", "amount": 1},
    ).json()
    batch = bft_client.post(
        "/bft/narwhal/batches",
        json={"operation_ids": [operation["operation_id"]]},
    ).json()["batch"]
    assert bft_client.post("/bft/hotstuff/proposals", json={"batch_id": batch["batch_id"]}).status_code == 409
    assert bft_client.post("/bft/hotstuff/proposals/missing/vote").status_code == 404
    assert bft_client.post("/bft/hotstuff/qc/missing/commit").status_code == 404

    bft_client.post(f"/bft/narwhal/batches/{batch['batch_id']}/certify-demo")
    proposal = bft_client.post("/bft/hotstuff/proposals", json={"batch_id": batch["batch_id"]}).json()
    qc = bft_client.post(f"/bft/hotstuff/proposals/{proposal['proposal_id']}/form-qc-demo").json()
    assert bft_client.post(f"/bft/hotstuff/qc/{qc['qc_id']}/commit").status_code == 200
    assert bft_client.post(f"/bft/hotstuff/qc/{qc['qc_id']}/commit").status_code == 409

    assert bft_client.post("/bft/swim/ping/99?simulate_success=false").status_code == 404
    assert bft_client.post("/bft/swim/gossip", json={"source_node_id": 1, "updates": []}).status_code == 400

    raw_operation = operation_store.create(sample_operation_input)
    assert bft_client.post(f"/bft/operations/{raw_operation.operation_id}/commit").status_code == 409
    with pytest.raises(ValueError):
        operation_store.transition(
            raw_operation.operation_id,
            OperationStatus.COMMITTED,
            ProtocolName.HOTSTUFF,
            "invalid",
        )
