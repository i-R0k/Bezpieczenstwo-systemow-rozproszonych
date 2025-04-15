# tests/test_animals.py
import pytest
from fastapi.testclient import TestClient

# 'client' zostaje udostępniony przez fixture z conftest.py

def test_create_animal(client: TestClient):
    # Przyjmujemy, że rekord właściciela o id=1 istnieje.
    payload = {
        "name": "Burek",
        "species": "dog",
        "breed": "Labrador",
        "gender": "male",
        "birth_date": "2020-01-01",
        "age": 3,
        "weight": 25.5,
        "microchip_number": "123456789012345",  # 15 cyfr
        "notes": "Bardzo przyjacielski pies",
        "owner_id": 1,
        "last_visit": "2023-04-11T10:00:00"
    }
    response = client.post("/animals/", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert "id" in data
    assert data["name"] == payload["name"]
    assert data["microchip_number"] == payload["microchip_number"]

def test_get_animals(client: TestClient):
    response = client.get("/animals/")
    assert response.status_code == 200, response.text
    data = response.json()
    # Sprawdzamy, że odpowiedź jest listą, a jeśli zawiera jakieś rekordy, to posiada wymagane pola
    assert isinstance(data, list)
    if data:
        assert "id" in data[0]
        assert "name" in data[0]

def test_update_animal(client: TestClient):
    # Najpierw tworzymy nowe zwierzę do aktualizacji
    payload = {
        "name": "Reksio",
        "species": "dog",
        "breed": "Mieszaniec",
        "gender": "male",
        "birth_date": "2019-05-01",
        "age": 4,
        "weight": 20.0,
        "microchip_number": "987654321012345",  # 15 cyfr
        "notes": "Pierwotna nazwa",
        "owner_id": 1,
        "last_visit": "2023-04-10T09:00:00"
    }
    create_resp = client.post("/animals/", json=payload)
    assert create_resp.status_code == 201, create_resp.text
    animal_id = create_resp.json()["id"]

    update_payload = {"name": "Reksio Updated", "weight": 21.0}
    update_resp = client.put(f"/animals/{animal_id}", json=update_payload)
    assert update_resp.status_code == 200, update_resp.text
    updated_data = update_resp.json()
    assert updated_data["name"] == update_payload["name"]
    assert updated_data["weight"] == update_payload["weight"]

def test_delete_animal(client: TestClient):
    # Tworzymy zwierzę, które potem usuniemy
    payload = {
        "name": "DoDelete",
        "species": "cat",
        "breed": "Siamese",
        "gender": "female",
        "birth_date": "2021-01-01",
        "age": 2,
        "weight": 4.5,
        "microchip_number": "111111111111111",  # 15 cyfr
        "notes": "Do usunięcia",
        "owner_id": 1,
        "last_visit": None
    }
    create_resp = client.post("/animals/", json=payload)
    assert create_resp.status_code == 201, create_resp.text
    animal_id = create_resp.json()["id"]

    del_resp = client.delete(f"/animals/{animal_id}")
    assert del_resp.status_code == 200, del_resp.text

    # Sprawdzamy, że rekord już nie istnieje
    get_resp = client.get(f"/animals/{animal_id}")
    assert get_resp.status_code == 404
