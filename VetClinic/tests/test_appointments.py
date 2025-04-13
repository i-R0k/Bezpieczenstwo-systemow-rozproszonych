# tests/test_appointments.py
import pytest
from fastapi.testclient import TestClient

# 'client' udostępniany jest przez conftest.py

def test_create_appointment(client: TestClient):
    # Zakładamy, że istnieją już rekordy:
    # - Zwierzę o id=1 (utworzone podczas testów animals)
    # - Lekarz o id=2
    # - Klient o id=1
    payload = {
        "visit_datetime": "2023-05-15T09:30:00",
        "reason": "Konsultacja zdrowotna, badanie rutynowe",
        "status": "zaplanowana",
        "doctor_id": 2,
        "animal_id": 1,
        "owner_id": 1,
        "notes": "Planowana wizyta kontrolna"
    }
    response = client.post("/appointments/", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert "id" in data
    assert data["status"] == payload["status"]

def test_get_appointments(client: TestClient):
    response = client.get("/appointments/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "id" in data[0]
        assert "visit_datetime" in data[0]

def test_update_appointment(client: TestClient):
    # Najpierw tworzymy wizytę
    payload = {
        "visit_datetime": "2023-05-20T10:00:00",
        "reason": "Szczepienie",
        "status": "zaplanowana",
        "doctor_id": 2,
        "animal_id": 1,
        "owner_id": 1,
        "notes": "Pierwsze szczepienie"
    }
    create_resp = client.post("/appointments/", json=payload)
    assert create_resp.status_code == 201, create_resp.text
    appointment_id = create_resp.json()["id"]

    update_payload = {"status": "zakończona", "notes": "Wizyta zakończona bez komplikacji"}
    update_resp = client.put(f"/appointments/{appointment_id}", json=update_payload)
    assert update_resp.status_code == 200, update_resp.text
    updated_data = update_resp.json()
    assert updated_data["status"] == "zakończona"
    assert updated_data["notes"] == update_payload["notes"]

def test_delete_appointment(client: TestClient):
    # Tworzymy wizytę, którą potem usuniemy
    payload = {
        "visit_datetime": "2023-05-25T11:00:00",
        "reason": "Kontrola po zabiegu",
        "status": "zaplanowana",
        "doctor_id": 2,
        "animal_id": 1,
        "owner_id": 1,
        "notes": "Kontrola"
    }
    create_resp = client.post("/appointments/", json=payload)
    assert create_resp.status_code == 201, create_resp.text
    appointment_id = create_resp.json()["id"]

    del_resp = client.delete(f"/appointments/{appointment_id}")
    assert del_resp.status_code == 200, del_resp.text

    # Sprawdzamy, że wizyty już nie ma
    get_resp = client.get(f"/appointments/{appointment_id}")
    assert get_resp.status_code == 404
