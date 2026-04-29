from __future__ import annotations


def test_bft_dashboard_serves_html_with_expected_fetch_endpoints(bft_client) -> None:
    response = bft_client.get("/bft/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text
    for endpoint in (
        "/bft/status",
        "/bft/events",
        "/bft/swim/status",
        "/bft/hotstuff/status",
        "/bft/communication/log",
    ):
        assert endpoint in html


def test_communication_log_contract_and_limit_validation(bft_client) -> None:
    response = bft_client.get("/bft/communication/log")
    assert response.status_code == 200
    payload = response.json()
    assert "messages" in payload
    assert "count" in payload

    invalid = bft_client.get("/bft/communication/log?limit=-1")
    assert invalid.status_code in {400, 422}


def test_communication_log_contains_bft_events_after_demo_activity(bft_client) -> None:
    submitted = bft_client.post(
        "/bft/client/submit",
        json={
            "sender": "alice",
            "recipient": "bob",
            "amount": 10.5,
            "payload": {"kind": "dashboard-demo"},
        },
    )
    assert submitted.status_code == 200

    demo = bft_client.post("/bft/demo/run")
    assert demo.status_code == 200

    response = bft_client.get("/bft/communication/log?limit=100")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] > 0
    protocols = {message["protocol"] for message in payload["messages"]}
    assert {"HOTSTUFF", "NARWHAL"} & protocols
    assert any(message["message_kind"] for message in payload["messages"])
