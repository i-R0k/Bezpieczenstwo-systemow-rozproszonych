"""
Przykładowe testy dla endpointów użytkowników.
Wykorzystaj framework pytest i narzędzie TestClient z FastAPI.
"""

from fastapi.testclient import TestClient
from src.app.main import app

client = TestClient(app)

def test_create_user():
    # Przykładowe dane użytkownika
    user_data = {
        "first_name": "Jan",
        "last_name": "Kowalski",
        "email": "jan.kowalski@example.com",
        "password": "tajnehaslo"
    }
    response = client.post("/users/", json=user_data)
    # W zależności od implementacji możesz zmodyfikować oczekiwany status i dane
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "jan.kowalski@example.com"
