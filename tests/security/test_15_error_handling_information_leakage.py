from __future__ import annotations


FORBIDDEN_LEAKS = [
    "Traceback",
    'File "',
    "sqlalchemy.exc",
    "private_key",
    "LEADER_PRIV_KEY",
    "BFT_ADMIN_TOKEN",
]


def _assert_no_error_leakage(response) -> None:
    for marker in FORBIDDEN_LEAKS:
        assert marker not in response.text


def test_bft_error_responses_do_not_leak_tracebacks_or_secrets(security_bft_client):
    responses = [
        security_bft_client.get("/bft/operations/not-found"),
        security_bft_client.post("/bft/faults/rules", json={"fault_type": "UNKNOWN"}),
        security_bft_client.post("/bft/crypto/verify", json={"not": "a signed message"}),
    ]

    for response in responses:
        assert response.status_code in {400, 404, 409, 422}
        _assert_no_error_leakage(response)


def test_rpc_error_responses_do_not_leak_tracebacks_or_secrets(security_full_app_client):
    responses = [
        security_full_app_client.post("/rpc/propose_block", json={"bad": "payload"}),
        security_full_app_client.post("/rpc/commit_block", json={"bad": "payload"}),
        security_full_app_client.get("/rpc/not-found"),
    ]

    for response in responses:
        assert response.status_code in {400, 404, 409, 422}
        _assert_no_error_leakage(response)


def test_vetclinic_crud_error_responses_do_not_leak_tracebacks_or_secrets(security_full_app_client):
    responses = [
        security_full_app_client.get("/users/999999999"),
        security_full_app_client.post("/users/register", json={"email": "invalid"}),
        security_full_app_client.get("/medical-records/999999999"),
        security_full_app_client.post("/appointments/", json={"doctor_id": "bad"}),
    ]

    for response in responses:
        assert response.status_code in {400, 401, 403, 404, 409, 422}
        _assert_no_error_leakage(response)

