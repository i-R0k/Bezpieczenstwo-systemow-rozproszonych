import pytest
import uuid
import re
import pyotp
import datetime  # używamy jeśli potrzebne w testach, choć warning dotyczy logiki auth, a nie testów
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app  # Główny punkt FastAPI
from app.core.database import Base, get_db

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

# Fixtura generująca unikalnego użytkownika z unikalnym adresem email
@pytest.fixture
def new_user():
    unique_email = f"jan.kkowalski_{uuid.uuid4().hex[:6]}@example.com"
    return {
        "first_name": "Jan",
        "last_name": "Kowalski",
        "email": unique_email,
        "password": "tajnehaslo",
        "role": "klient",
        "phone_number": "+48123456789",
        "address": "ul. Przykładowa 1",
        "postal_code": "00-001 Warszawa",
        "totp_secret": None,
        "totp_confirmed": False,
    }

def register_user(user):
    """Pomocnicza funkcja rejestrująca użytkownika."""
    response = client.post("/users/register", json=user)
    assert response.status_code in (200, 201), f"Rejestracja nie powiodła się: {response.text}"
    return response.json()

def register_and_get_provisioning_uri(user):
    """
    Rejestruje użytkownika oraz wykonuje logowanie bez przekazywania totp_code.
    Zwraca provisioning URI.
    """
    register_user(user)
    payload = {
        "email": user["email"],
        "password": user["password"]
    }
    response = client.post("/users/login", json=payload)
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert data.get("need_totp") is True, "Oczekiwano flagi need_totp ustawionej na True"
    assert "totp_uri" in data, "Brak provisioning URI w odpowiedzi"
    return data["totp_uri"]

def test_register_user(new_user):
    """Test rejestracji użytkownika."""
    data = register_user(new_user)
    assert data["email"] == new_user["email"]
    assert "id" in data

def test_login_first_time(new_user):
    """
    Pierwsze logowanie – użytkownik nie przesyła pola totp_code.
    Endpoint powinien zwrócić status 201 oraz provisioning URI.
    """
    totp_uri = register_and_get_provisioning_uri(new_user)
    # Sprawdzamy, czy provisioning URI zawiera secret
    assert re.search(r"secret=([^&]+)", totp_uri), "Nie znaleziono secretu w totp_uri"
    # Funkcja testowa nie zwraca wartości – jedynie asercje

def test_confirm_totp(new_user):
    """
    Test konfiguracji TOTP:
      - Rejestrujemy i logujemy użytkownika, otrzymując provisioning URI.
      - Wyciągamy secret z URI, generujemy kod TOTP i wysyłamy go do endpointu /users/confirm-totp.
    """
    totp_uri = register_and_get_provisioning_uri(new_user)
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
      - Rejestrujemy i logujemy użytkownika, otrzymując provisioning URI.
      - Potwierdzamy konfigurację TOTP.
      - Wykonujemy logowanie z poprawnym totp_code, oczekując tokenu JWT.
    """
    totp_uri = register_and_get_provisioning_uri(new_user)
    # Wyciągamy secret z provisioning URI
    match = re.search(r"secret=([^&]+)", totp_uri)
    assert match, "Nie znaleziono secretu w totp_uri"
    secret = match.group(1)
    totp = pyotp.TOTP(secret)

    # Potwierdzamy TOTP
    current_code = totp.now()
    payload_confirm = {
        "email": new_user["email"],
        "totp_code": current_code
    }
    resp_confirm = client.post("/users/confirm-totp", json=payload_confirm)
    assert resp_confirm.status_code == 200, f"Expected 200 on confirm, got {resp_confirm.status_code}: {resp_confirm.text}"

    # Logowanie z poprawnym totp_code
    current_code = totp.now()  # Nowy kod, gdyż kod zmienia się co 30 sekund
    payload_login = {
        "email": new_user["email"],
        "password": new_user["password"],
        "totp_code": current_code
    }
    resp_login = client.post("/users/login", json=payload_login)
    assert resp_login.status_code == 200, f"Expected 200, got {resp_login.status_code}: {resp_login.text}"
    assert "access_token" in resp_login.json()
