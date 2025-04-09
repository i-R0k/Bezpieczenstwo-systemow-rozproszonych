import pytest
import uuid
import re
import pyotp
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.main import app  # Główny punkt FastAPI
from src.app.database import Base, get_db

# Konfiguracja testowej bazy SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Resetujemy bazę przy starcie testów
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Override zależności get_db
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Fixture generujące unikalnego użytkownika
@pytest.fixture
def new_user():
    unique_email = f"jan.kowalski_{uuid.uuid4().hex[:6]}@example.com"
    return {
        "first_name": "Jan",
        "last_name": "Kowalski",
        "email": "jan.kkowalski@example.com",
        "password": "tajnehaslo",
        "role": "klient",
        "phone_number": "+48123456789",
        "address": "ul. Przykładowa 1",
        "postal_code": "00-001 Warszawa"
    }

def test_register_user(new_user):
    """Test rejestracji użytkownika."""
    response = client.post("/users/register", json=new_user)
    assert response.status_code in (200, 201), f"Status code: {response.status_code}, response: {response.text}"
    data = response.json()
    assert data["email"] == new_user["email"]
    assert "id" in data

def test_login_first_time(new_user):
    """
    Pierwsze logowanie – użytkownik nie przesyła pola totp_code.
    Wówczas endpoint powinien wygenerować totp_secret i provisioning URI oraz zwrócić status 201.
    """
    payload = {
        "email": new_user["email"],
        "password": new_user["password"]
    }
    response = client.post("/users/login", json=payload)
    # Spodziewamy się statusu 201, co oznacza, że TOTP nie było skonfigurowane
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert data.get("need_totp") is True
    assert "totp_uri" in data
    # Zwracamy totp_uri, aby użyć go w kolejnych testach
    return data["totp_uri"]

def test_confirm_totp(new_user):
    """
    Test konfiguracji TOTP:
     - Wykonujemy pierwsze logowanie, aby otrzymać provisioning URI.
     - Wyciągamy secret z URI, generujemy aktualny 6-cyfrowy kod TOTP
       i wysyłamy go do endpointu /users/confirm-totp.
    """
    totp_uri = test_login_first_time(new_user)
    # Wyciągamy secret z provisioning URI
    match = re.search(r"secret=([^&]+)", totp_uri)
    assert match, "Nie znaleziono secretu w totp_uri"
    secret = match.group(1)
    totp = pyotp.TOTP(secret)
    current_code = totp.now()
    payload_confirm = {
        "email": new_user["email"],
        "totp_code": current_code
    }
    resp_confirm = client.post("/users/confirm-totp", json=payload_confirm)
    assert resp_confirm.status_code == 200, f"Expected 200, got {resp_confirm.status_code}: {resp_confirm.text}"
    data_confirm = resp_confirm.json()
    assert "TOTP confirmed" in data_confirm.get("detail", "")

def test_login_with_totp(new_user):
    """
    Test logowania z TOTP:
     - Najpierw konfigurujemy TOTP (jeśli nie był skonfigurowany), 
       a następnie logujemy się podając email, hasło i kod TOTP.
    """
    # Konfigurujemy TOTP – wykonujemy pierwsze logowanie i potwierdzamy TOTP
    totp_uri = test_login_first_time(new_user)
    match = re.search(r"secret=([^&]+)", totp_uri)
    assert match, "Nie znaleziono secretu w totp_uri"
    secret = match.group(1)
    totp = pyotp.TOTP(secret)
    current_code = totp.now()
    payload_confirm = {
        "email": new_user["email"],
        "totp_code": current_code
    }
    resp_confirm = client.post("/users/confirm-totp", json=payload_confirm)
    assert resp_confirm.status_code == 200, f"Expected 200 on TOTP confirm, got {resp_confirm.status_code}"
    
    # Teraz logowanie z kompletnym payload: email, hasło i totp_code
    current_code = totp.now()  # generujemy nowy kod, bo kod zmienia się co 30 sekund
    payload_login = {
        "email": new_user["email"],
        "password": new_user["password"],
        "totp_code": current_code
    }
    resp_final = client.post("/users/login", json=payload_login)
    assert resp_final.status_code == 200, f"Expected 200, got {resp_final.status_code}: {resp_final.text}"
    data_final = resp_final.json()
    assert "access_token" in data_final
