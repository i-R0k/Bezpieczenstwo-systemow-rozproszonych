"""
Przykładowe testy dla endpointów wizyt.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_appointments():
    response = client.get("/appointments/")
    assert response.status_code == 200
    data = response.json()
    assert "appointments" in data
