from __future__ import annotations


SECRET_MARKERS = ("private_key", "BFT_ADMIN_TOKEN", "LEADER_PRIV_KEY", "private_key_b64")


def test_dashboard_html_does_not_expose_secret_markers(security_bft_client) -> None:
    response = security_bft_client.get("/bft/dashboard")
    assert response.status_code == 200
    body = response.text
    for marker in SECRET_MARKERS:
        assert marker not in body


def test_communication_log_does_not_expose_private_key_material(security_bft_client) -> None:
    security_bft_client.post(
        "/bft/client/submit",
        json={
            "sender": "alice",
            "recipient": "bob",
            "amount": 10.5,
            "payload": {"kind": "dashboard-security"},
        },
    )
    response = security_bft_client.get("/bft/communication/log")
    assert response.status_code == 200
    body = response.text
    assert "private_key_b64" not in body
    assert "PRIVATE KEY" not in body


def test_dashboard_uses_only_safe_get_requests_for_data_fetching(security_bft_client) -> None:
    response = security_bft_client.get("/bft/dashboard")
    assert response.status_code == 200
    html = response.text.lower()
    assert "fetch(" in html
    assert "method: 'post'" not in html
    assert 'method: "post"' not in html
    assert "method:'post'" not in html
    assert 'method:"post"' not in html
    assert "/bft/demo/run" not in html
    assert "/bft/faults/rules" not in html
