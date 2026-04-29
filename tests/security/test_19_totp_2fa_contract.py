from __future__ import annotations

import pyotp

from vetclinic_api.security.totp import generate_totp_secret, provisioning_uri, verify_totp_code


def test_totp_helpers_accept_current_code_and_reject_bad_code() -> None:
    secret = generate_totp_secret()
    uri = provisioning_uri(secret, "alice@example.test")
    assert "otpauth://" in uri

    code = pyotp.TOTP(secret).now()
    assert verify_totp_code(secret, code) is True
    assert verify_totp_code(secret, "000000") is False


def test_security_2fa_demo_setup_and_verify(security_full_app_client) -> None:
    setup = security_full_app_client.post(
        "/security/2fa/demo/setup",
        json={"account_name": "alice@example.test"},
    )
    assert setup.status_code == 200
    payload = setup.json()
    assert payload["account_name"] == "alice@example.test"
    assert "otpauth://" in payload["provisioning_uri"]

    code = pyotp.TOTP(payload["secret"]).now()
    valid = security_full_app_client.post(
        "/security/2fa/demo/verify",
        json={"account_name": "alice@example.test", "code": code},
    )
    assert valid.status_code == 200
    assert valid.json()["valid"] is True

    invalid = security_full_app_client.post(
        "/security/2fa/demo/verify",
        json={"account_name": "alice@example.test", "code": "000000"},
    )
    assert invalid.status_code == 200
    assert invalid.json()["valid"] is False


def test_security_2fa_demo_delete_requires_token_in_strict_mode(security_full_app_client, monkeypatch) -> None:
    monkeypatch.setenv("BFT_SECURITY_MODE", "strict")
    monkeypatch.setenv("BFT_ADMIN_TOKEN", "secret-token")
    response = security_full_app_client.delete("/security/2fa/demo")
    assert response.status_code in {401, 403}


def test_bft_submit_secure_demo_strict_requires_and_accepts_totp(security_bft_client, monkeypatch) -> None:
    monkeypatch.setenv("BFT_SECURITY_MODE", "strict")
    monkeypatch.setenv("BFT_ADMIN_TOKEN", "secret-token")
    payload = {
        "sender": "alice",
        "recipient": "bob",
        "amount": 12.5,
        "payload": {"kind": "totp-demo"},
    }

    rejected = security_bft_client.post("/bft/client/submit-secure-demo", json=payload)
    assert rejected.status_code in {401, 403}

    secret = generate_totp_secret()
    accepted = security_bft_client.post(
        "/bft/client/submit-secure-demo",
        json={**payload, "totp_secret": secret, "totp_code": pyotp.TOTP(secret).now()},
    )
    assert accepted.status_code == 200
    body = accepted.json()
    assert body["totp_required"] is True
    assert body["totp_verified"] is True
    assert body["operation"]["status"] == "RECEIVED"
