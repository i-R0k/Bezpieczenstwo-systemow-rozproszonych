from __future__ import annotations


def test_observability_router_contract(bft_client):
    assert bft_client.get("/bft/observability/health").status_code == 200
    metrics = bft_client.get("/bft/observability/metrics")
    assert metrics.status_code == 200
    assert "bft_operations_submitted_total" in metrics.text
    assert bft_client.get("/bft/observability/metrics/snapshot").status_code == 200
    demo = bft_client.post("/bft/demo/run")
    assert demo.status_code == 200
    assert demo.json()["status"] == "ok"
    assert bft_client.get("/bft/demo/last-report").status_code == 200
    assert bft_client.delete("/bft/demo/last-report").status_code == 200
    assert bft_client.get("/bft/demo/last-report").status_code == 404
