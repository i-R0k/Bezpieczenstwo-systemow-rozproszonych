from __future__ import annotations

import pytest


@pytest.mark.bft
@pytest.mark.contract
def test_router_contract_endpoints_are_present(bft_client):
    for path in ["/bft/architecture", "/bft/protocols", "/bft/quorum", "/bft/events"]:
        assert bft_client.get(path).status_code == 200

    operation = bft_client.post(
        "/bft/client/submit",
        json={"sender": "alice", "recipient": "bob", "amount": 1},
    )
    assert operation.status_code == 200
    operation_id = operation.json()["operation_id"]
    assert bft_client.get("/bft/operations").status_code == 200
    assert bft_client.get(f"/bft/operations/{operation_id}").status_code == 200
    assert bft_client.get(f"/bft/operations/{operation_id}/trace").status_code == 200
    assert bft_client.post(f"/bft/operations/{operation_id}/run-demo").status_code == 200

    second = bft_client.post(
        "/bft/client/submit",
        json={"sender": "carol", "recipient": "dave", "amount": 2},
    ).json()
    assert bft_client.post(
        "/bft/narwhal/batches",
        json={"operation_ids": [second["operation_id"]]},
    ).status_code == 200
    assert bft_client.get("/bft/narwhal/batches").status_code == 200
    assert bft_client.get("/bft/narwhal/dag").status_code == 200
    assert bft_client.get("/bft/narwhal/tips").status_code == 200

    assert bft_client.get("/bft/hotstuff/status").status_code == 200
    assert bft_client.post("/bft/hotstuff/view-change-demo").status_code == 200

    assert bft_client.post("/bft/swim/bootstrap").status_code == 200
    assert bft_client.get("/bft/swim/members").status_code == 200
    assert bft_client.get("/bft/swim/status").status_code == 200
