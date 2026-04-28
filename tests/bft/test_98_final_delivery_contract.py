from __future__ import annotations


def test_final_demo_and_observability_contract(bft_client):
    demo_response = bft_client.post("/bft/demo/run")
    assert demo_response.status_code == 200
    report = demo_response.json()
    assert report["status"] == "ok"

    last_report_response = bft_client.get("/bft/demo/last-report")
    assert last_report_response.status_code == 200
    assert last_report_response.json()["report_id"] == report["report_id"]

    assert bft_client.get("/bft/observability/health").status_code != 500
    assert bft_client.get("/bft/observability/metrics").status_code != 500
    assert bft_client.get("/bft/architecture").status_code != 500
    assert bft_client.get("/bft/status").status_code != 500

    trace_response = bft_client.get(f"/bft/operations/{report['operation_id']}/trace")
    assert trace_response.status_code == 200
    trace = trace_response.json()
    status_values = {entry["to_status"] for entry in trace["transitions"]}
    assert "EXECUTED" in status_values

    assert report["checkpoint_id"]
    assert report["recovered_node_id"] == 3
    assert report["metrics_snapshot"]
