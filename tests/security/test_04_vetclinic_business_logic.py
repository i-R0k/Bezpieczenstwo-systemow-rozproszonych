from __future__ import annotations

import uuid


def test_vetclinic_detail_endpoints_for_unknown_ids_do_not_return_500(security_full_app_client):
    paths = [
        "/users/999999999",
        "/doctors/999999999",
        "/animals/999999999",
        "/appointments/999999999",
        "/medical-records/999999999",
        "/invoices/999999999",
    ]

    for path in paths:
        response = security_full_app_client.get(path)
        assert response.status_code != 500, path


def test_user_create_or_update_mass_assignment_fields_are_not_exposed(security_full_app_client):
    unique = uuid.uuid4().hex[:8]
    create_payload = {
        "first_name": "Alice",
        "last_name": "Security",
        "password": "StrongPassword123!",
        "role": "client",
        "email": f"alice-{unique}@example.com",
        "phone_number": "123456789",
        "address": "Security Street 1",
        "postal_code": "12-345",
        "wallet_address": "wallet-demo",
        "is_admin": True,
        "is_superuser": True,
        "is_paid": True,
    }

    create = security_full_app_client.post("/users/register", json=create_payload)
    assert create.status_code != 500
    if create.headers.get("content-type", "").startswith("application/json"):
        body = create.json()
        assert "is_admin" not in body
        assert "is_superuser" not in body
        assert "is_paid" not in body

    update = security_full_app_client.put(
        "/users/999999999",
        json={"role": "admin", "is_admin": True, "is_superuser": True, "is_paid": True},
    )
    assert update.status_code != 500
    if update.headers.get("content-type", "").startswith("application/json"):
        body = update.json()
        assert "is_admin" not in body
        assert "is_superuser" not in body
        assert "is_paid" not in body


def test_invoice_and_payment_negative_amount_or_unknown_invoice_is_controlled(security_full_app_client):
    invoice = security_full_app_client.post("/invoices/", json={"client_id": 999999999, "amount": "-10.00"})
    stripe = security_full_app_client.post("/payments/stripe/999999999")
    payu = security_full_app_client.post("/payments/payu/999999999")

    assert invoice.status_code != 500
    assert stripe.status_code != 500
    assert payu.status_code != 500


def test_appointment_unknown_references_do_not_return_500(security_full_app_client):
    payload = {
        "visit_datetime": "2030-01-01T10:00:00",
        "reason": "security test",
        "treatment": "none",
        "priority": "normalna",
        "weight": 10.0,
        "fee": 100.0,
        "doctor_id": 999999999,
        "animal_id": 999999999,
        "owner_id": 999999999,
        "facility_id": 999999999,
        "notes": "unknown references",
    }

    response = security_full_app_client.post("/appointments/", json=payload)

    assert response.status_code != 500


def test_medical_record_long_description_does_not_return_500(security_full_app_client):
    payload = {
        "appointment_id": 999999999,
        "animal_id": 999999999,
        "description": "x" * 20_000,
    }

    response = security_full_app_client.post("/medical-records/", json=payload)

    assert response.status_code != 500


def test_idor_smoke_current_demo_behavior_for_unknown_detail_does_not_leak_data(security_full_app_client):
    response = security_full_app_client.get("/medical-records/987654321")

    assert response.status_code in {401, 403, 404, 422}
    assert "description" not in response.text.lower()

