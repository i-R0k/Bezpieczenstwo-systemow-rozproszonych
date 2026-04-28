from __future__ import annotations


def test_gossip_incarnation_ordering_and_status_strength(security_bft_client):
    assert security_bft_client.post("/bft/swim/bootstrap").status_code == 200

    stale = security_bft_client.post(
        "/bft/swim/gossip",
        json={
            "source_node_id": 1,
            "updates": [{"node_id": 2, "status": "DEAD", "incarnation": -1, "observed_by": 1}],
        },
    )
    assert stale.status_code == 200
    assert security_bft_client.get("/bft/swim/members/2").json()["status"] == "ALIVE"

    newer = security_bft_client.post(
        "/bft/swim/gossip",
        json={
            "source_node_id": 1,
            "updates": [{"node_id": 2, "status": "SUSPECT", "incarnation": 5, "observed_by": 1}],
        },
    )
    assert newer.status_code == 200
    member = security_bft_client.get("/bft/swim/members/2").json()
    assert member["status"] == "SUSPECT"
    assert member["incarnation"] == 5

    same_incarnation_dead = security_bft_client.post(
        "/bft/swim/gossip",
        json={
            "source_node_id": 1,
            "updates": [{"node_id": 2, "status": "DEAD", "incarnation": 5, "observed_by": 1}],
        },
    )
    assert same_incarnation_dead.status_code == 200
    assert security_bft_client.get("/bft/swim/members/2").json()["status"] == "DEAD"


def test_dead_node_mark_alive_increments_incarnation(security_bft_client):
    assert security_bft_client.post("/bft/swim/bootstrap").status_code == 200
    dead = security_bft_client.put("/bft/swim/members/2/dead").json()
    alive = security_bft_client.put("/bft/swim/members/2/alive").json()

    assert alive["status"] == "ALIVE"
    assert alive["incarnation"] > dead["incarnation"]


def test_ping_unknown_node_and_ping_self_are_controlled(security_bft_client):
    assert security_bft_client.post("/bft/swim/bootstrap").status_code == 200

    unknown = security_bft_client.post("/bft/swim/ping/999999")
    self_ping = security_bft_client.post("/bft/swim/ping/1")

    assert unknown.status_code != 500
    assert self_ping.status_code != 500

