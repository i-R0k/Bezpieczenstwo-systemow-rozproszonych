import pytest
import datetime
from fastapi.testclient import TestClient
from vetclinic_api.routers import users
from vetclinic_api.schemas.users import ClientCreate, UserLogin, PasswordReset, ConfirmTOTP
from unittest.mock import MagicMock
import pyotp

# Załóż, że masz FastAPI app:
from vetclinic_api.main import app

client = TestClient(app)

def example_client():
    return {
        "id": 1,
        "first_name": "Anna",
        "last_name": "Nowak",
        "email": "a@b.com",
        "phone_number": "+48123456789",
        "address": "ul. Testowa 1",
        "postal_code": "00-001 Warszawa",
        "role": "klient",
        "wallet_address": "0x123"
    }

# --- REJESTRACJA ---
def test_register_client_success(monkeypatch):
    # dobry klient
    monkeypatch.setattr(users, "create_client", lambda db, u: {**example_client(), **u.model_dump()})
    data = example_client()
    data["password"] = "Passw0rd!"
    r = client.post("/users/register", json=data)
    assert r.status_code == 201
    assert r.json()["first_name"] == "Anna"

def test_register_client_wrong_role(monkeypatch):
    data = example_client()
    data["password"] = "Passw0rd!"
    data["role"] = "admin"
    r = client.post("/users/register", json=data)
    assert r.status_code == 400
    assert "Self-registration allowed" in r.json()["detail"]

# --- LISTA I GET ---
def test_get_users(monkeypatch):
    monkeypatch.setattr(users, "list_clients", lambda db: [example_client()])
    r = client.get("/users/")
    assert r.status_code == 200
    assert r.json()[0]["id"] == 1

def test_get_user_found(monkeypatch):
    monkeypatch.setattr(users, "get_client", lambda db, uid: example_client())
    r = client.get("/users/1")
    assert r.status_code == 200
    assert r.json()["email"] == "a@b.com"

def test_get_user_not_found(monkeypatch):
    monkeypatch.setattr(users, "get_client", lambda db, uid: None)
    r = client.get("/users/9999")
    assert r.status_code == 404

# --- UPDATE ---
def test_update_user_success(monkeypatch):
    monkeypatch.setattr(users, "update_client", lambda db, uid, d: example_client())
    patch = {"first_name": "Joanna", "wallet_address": "0x123"}
    r = client.put("/users/1", json=patch)
    assert r.status_code == 200

def test_update_user_notfound(monkeypatch):
    monkeypatch.setattr(users, "update_client", lambda db, uid, d: None)
    patch = {"first_name": "Z", "wallet_address": "0x123"}
    r = client.put("/users/88", json=patch)
    assert r.status_code == 404

# --- DELETE SINGLE ---
def test_delete_user_success(monkeypatch):
    monkeypatch.setattr(users, "delete_client", lambda db, uid: True)
    r = client.delete("/users/1")
    assert r.status_code == 204

def test_delete_user_notfound(monkeypatch):
    monkeypatch.setattr(users, "delete_client", lambda db, uid: False)
    r = client.delete("/users/777")
    assert r.status_code == 404

# --- DELETE MANY ---
def test_delete_many(monkeypatch):
    monkeypatch.setattr(users, "delete_client", lambda db, uid: True)
    r = client.request("DELETE", "/users/", json=[1, 2, 3])
    assert r.status_code == 204

# --- CHANGE PASSWORD ---
def test_change_password_success(monkeypatch):
    fake_user = MagicMock()
    fake_user.password_hash = "h1"
    monkeypatch.setattr(users, "get_user_by_email", lambda db, email: fake_user)
    monkeypatch.setattr(users, "verify_password", lambda pw, h: True)
    monkeypatch.setattr(users, "get_password_hash", lambda pw: "h2")
    data = {
        "email": "a@b.com",
        "old_password": "foo",
        "new_password": "bar",
        "reset_totp": False
    }
    r = client.post("/users/change-password", json=data)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_change_password_fail(monkeypatch):
    monkeypatch.setattr(users, "get_user_by_email", lambda db, email: None)
    data = {
        "email": "a@b.com",
        "old_password": "bad",
        "new_password": "bar",
        "reset_totp": False
    }
    r = client.post("/users/change-password", json=data)
    assert r.status_code == 400

# --- LOGIN (częściowe ścieżki) ---
def test_login_blocked(monkeypatch):
    user = MagicMock()
    user.locked_until = datetime.datetime.utcnow() + datetime.timedelta(minutes=1)
    monkeypatch.setattr(users, "get_user_by_email", lambda db, email: user)
    data = {"email": "a@b.com", "password": "pass"}
    r = client.post("/users/login", json=data)
    assert r.status_code == 423

def test_login_wrong(monkeypatch):
    monkeypatch.setattr(users, "get_user_by_email", lambda db, email: None)
    data = {"email": "a@b.com", "password": "bad"}
    r = client.post("/users/login", json=data)
    assert r.status_code == 400

def test_login_first(monkeypatch):
    user = MagicMock()
    user.locked_until = None
    user.failed_login_attempts = 0
    user.is_temporary = True
    user.password_hash = "x"
    user.id = 42 
    monkeypatch.setattr(users, "get_user_by_email", lambda db, email: user)
    monkeypatch.setattr(users, "verify_password", lambda p, h: True)
    data = {"email": "a@b.com", "password": "pass"}
    r = client.post("/users/login", json=data)
    assert r.status_code == 202

# --- TOTP SETUP ---
def test_setup_totp_success(monkeypatch):
    user = MagicMock()
    user.email = "a@b.com"
    monkeypatch.setattr(users, "get_user_by_email", lambda db, email: user)
    monkeypatch.setattr(pyotp, "random_base32", lambda: "KZQW4===")
    monkeypatch.setattr(pyotp.TOTP, "provisioning_uri", lambda self, name, issuer_name: "otpauth://totp/fake")
    monkeypatch.setattr(users, "generate_qr_code", lambda uri: MagicMock(save=lambda fn: None))
    r = client.post("/users/setup-totp", params={"email": "a@b.com"})
    assert r.status_code == 200
    assert "totp_uri" in r.json()

def test_setup_totp_nouser(monkeypatch):
    monkeypatch.setattr(users, "get_user_by_email", lambda db, email: None)
    r = client.post("/users/setup-totp", params={"email": "bad@b.com"})
    assert r.status_code == 404

# --- TOTP CONFIRM ---
def test_confirm_totp_success(monkeypatch):
    user = MagicMock()
    user.totp_secret = "ABC"
    monkeypatch.setattr(users, "get_user_by_email", lambda db, email: user)
    monkeypatch.setattr(pyotp.TOTP, "verify", lambda self, code: True)
    data = {"email": "a@b.com", "totp_code": "123456"}
    r = client.post("/users/confirm-totp", json=data)
    assert r.status_code == 200

def test_confirm_totp_fail(monkeypatch):
    user = MagicMock()
    user.totp_secret = "ABC"
    monkeypatch.setattr(users, "get_user_by_email", lambda db, email: user)
    monkeypatch.setattr(pyotp.TOTP, "verify", lambda self, code: False)
    data = {"email": "a@b.com", "totp_code": "999999"}
    r = client.post("/users/confirm-totp", json=data)
    assert r.status_code == 400

def test_confirm_totp_nouser(monkeypatch):
    monkeypatch.setattr(users, "get_user_by_email", lambda db, email: None)
    data = {"email": "no@b.com", "totp_code": "111111"}
    r = client.post("/users/confirm-totp", json=data)
    assert r.status_code == 404

def test_read_doctors(monkeypatch):
    fake_doctors = [
        {"id": 1, "first_name": "Jan", "last_name": "Kowalski", "email": "j.kowalski@lekarz.vetclinic.com",
         "specialization": "internista", "permit_number": "12345", "facility_id": 1}
    ]
    # Uwaga: podmień na poprawną ścieżkę do twojego routera!
    monkeypatch.setattr("vetclinic_api.routers.doctors.list_doctors", lambda db: fake_doctors)
    response = client.get("/doctors/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["first_name"] == "Jan"

def test_create_doctor_endpoint(monkeypatch):
    # Test z mockiem create_doctor
    def fake_create_doctor(db, doc_in):
        return ("password", {
            "id": 2, "first_name": doc_in.first_name, "last_name": doc_in.last_name,
            "email": doc_in.email, "specialization": doc_in.specialization,
            "permit_number": doc_in.permit_number, "facility_id": doc_in.facility_id
        })
    monkeypatch.setattr("vetclinic_api.crud.doctors.create_doctor", fake_create_doctor)
    # Mock db.query(Doctor).filter_by(email=...).first()
    class DummyDB:
        def query(self, model):
            class Query:
                def filter_by(self, **kwargs):
                    return self
                def first(self): return None
            return Query()
    monkeypatch.setattr("vetclinic_api.routers.doctors.get_db", lambda: DummyDB())
    data = {
        "first_name": "Jan", "last_name": "Nowak", "backup_email": "b@b.pl",
        "specialization": "internista", "permit_number": "12345", "facility_id": 1
    }
    response = client.post("/doctors/", json=data)
    assert response.status_code == 201
    assert response.json()["email"].endswith("@lekarz.vetclinic.com")

def test_read_doctor_found(monkeypatch):
    monkeypatch.setattr(
        "vetclinic_api.routers.doctors.get_doctor", 
        lambda db, id: {
            "id": 1,
            "first_name": "Anna",
            "last_name": "N.",
            "email": "a.n@lekarz.vetclinic.com",
            "specialization": "chirurg",
            "permit_number": "54321",
            "facility_id": 2
        }
    )
    response = client.get("/doctors/1")
    assert response.status_code == 200
    assert response.json()["first_name"] == "Anna"

def test_read_doctor_not_found(monkeypatch):
    monkeypatch.setattr("vetclinic_api.crud.doctors.get_doctor", lambda db, id: None)
    response = client.get("/doctors/99")
    assert response.status_code == 404

def test_update_doctor(monkeypatch):
    def fake_update_doctor(db, doctor_id, data):
        return {
            "id": doctor_id, "first_name": "Nowy", "last_name": "Lek", 
            "email": "n.l@lekarz.vetclinic.com",
            "specialization": "onkolog", "permit_number": "99999", 
            "facility_id": 1
        }
    monkeypatch.setattr("vetclinic_api.routers.doctors.update_doctor", fake_update_doctor)
    response = client.put("/doctors/1", json={
        "first_name": "Nowy",
        "last_name": "Lek",
        "specialization": "onkolog",
        "permit_number": "99999",
        "facility_id": 1,
        "email": "n.l@lekarz.vetclinic.com",
        "wallet_address": "0xABCDEF"  # jeśli wymagane
    })
    assert response.status_code == 200
    assert response.json()["first_name"] == "Nowy"

def test_update_doctor_not_found(monkeypatch):
    monkeypatch.setattr("vetclinic_api.routers.doctors.update_doctor", lambda db, did, d: None)
    response = client.put("/doctors/1", json={
        "first_name": "Nieistnieje",
        "last_name": "Kowalski",
        "specialization": "internista",
        "permit_number": "11111",
        "facility_id": 1,
        "email": "nieistnieje@lekarz.vetclinic.com",
        "wallet_address": "0xDEF"
    })
    assert response.status_code == 404

def test_delete_doctor_success(monkeypatch):
    monkeypatch.setattr("vetclinic_api.routers.doctors.delete_doctor", lambda db, did: True)
    response = client.delete("/doctors/1")
    assert response.status_code == 204

def test_delete_doctor_notfound(monkeypatch):
    monkeypatch.setattr("vetclinic_api.crud.doctors.delete_doctor", lambda db, did: False)
    response = client.delete("/doctors/999")
    assert response.status_code == 404
