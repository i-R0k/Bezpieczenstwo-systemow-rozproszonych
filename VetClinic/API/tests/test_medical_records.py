import pytest
from fastapi.testclient import TestClient

def test_create_medical_record(client: TestClient):
    payload = {
        "description": "Badanie krwi i ogólne badanie stanu zdrowia",
        "appointment_id": 1,
        "animal_id": 1
    }
    response = client.post("/medical_records/", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert "id" in data
    assert data["description"] == payload["description"]
    assert data["appointment_id"] == payload["appointment_id"]
    assert data["animal_id"] == payload["animal_id"]

def test_get_medical_records(client: TestClient):
    response = client.get("/medical_records/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    if data:
        rec = data[0]
        assert "id" in rec
        assert "description" in rec
        assert "appointment_id" in rec
        assert "animal_id" in rec

def test_get_single_medical_record_not_found(client: TestClient):
    response = client.get("/medical_records/9999")
    assert response.status_code == 404

def test_update_medical_record(client: TestClient):
    # najpierw tworzymy nowy rekord
    create_payload = {
        "description": "Wstępne badanie neurologiczne",
        "appointment_id": 1,
        "animal_id": 1
    }
    create_resp = client.post("/medical_records/", json=create_payload)
    assert create_resp.status_code == 201, create_resp.text
    record_id = create_resp.json()["id"]

    # teraz aktualizujemy tylko opis
    update_payload = {"description": "Aktualizacja: badanie neurologiczne z EEG"}
    update_resp = client.put(f"/medical_records/{record_id}", json=update_payload)
    assert update_resp.status_code == 200, update_resp.text
    updated = update_resp.json()
    assert updated["id"] == record_id
    assert updated["description"] == update_payload["description"]

def test_delete_medical_record(client: TestClient):
    # tworzymy rekord, który potem usuniemy
    payload = {
        "description": "Tymczasowy rekord do usunięcia",
        "appointment_id": 1,
        "animal_id": 1
    }
    create_resp = client.post("/medical_records/", json=payload)
    assert create_resp.status_code == 201, create_resp.text
    record_id = create_resp.json()["id"]

    del_resp = client.delete(f"/medical_records/{record_id}")
    # zwracamy 204 No Content
    assert del_resp.status_code == 204, del_resp.text

    # po usunięciu nie znajdziemy już wpisu
    get_resp = client.get(f"/medical_records/{record_id}")
    assert get_resp.status_code == 404
