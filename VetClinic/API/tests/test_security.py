import os
import jwt
import datetime
import re
import pyotp
import pytest
from passlib.context import CryptContext
from pathlib import Path

import vetclinic_api.core.security as sec
from vetclinic_api.models.users import Client, Doctor, Consultant

def test_password_hash_and_verify():
    pwd = "Very$ecret!"
    hashed = sec.get_password_hash(pwd)
    assert isinstance(hashed, str)
    assert sec.verify_password(pwd, hashed) is True
    assert sec.verify_password("wrong", hashed) is False

class DummyQuery:
    def __init__(self, result):
        self._res = result
    def filter(self, *args, **kwargs):
        return self
    def first(self):
        return self._res

class DummySession:
    def __init__(self, mapping):
        self._map = mapping
    def query(self, model):
        return DummyQuery(self._map.get(model, None))

@pytest.mark.parametrize("mapping,expected", [
    ({Client: "C", Doctor: None, Consultant: None}, "C"),
    ({Client: None, Doctor: "D", Consultant: None}, "D"),
    ({Client: None, Doctor: None, Consultant: "X"}, "X"),
    ({Client: None, Doctor: None, Consultant: None}, None),
])
def test_get_user_by_email(mapping, expected):
    session = DummySession(mapping)
    result = sec.get_user_by_email(session, "foo@bar")
    assert result == expected

def test_create_access_token_default_and_custom_expiry(monkeypatch):
    # Ustawiamy znany klucz, żebyśmy mogli rozkodować JWT
    monkeypatch.setattr(sec, "SECRET_KEY", "testkey123")
    # default expiry = 1h
    token1 = sec.create_access_token({"sub": "user1"})
    data1 = jwt.decode(token1, "testkey123", algorithms=[sec.ALGORITHM])
    assert data1["sub"] == "user1"
    assert "exp" in data1
    exp1 = datetime.datetime.fromtimestamp(data1["exp"], datetime.timezone.utc)
    now = datetime.datetime.now(datetime.timezone.utc)
    assert now < exp1 <= now + datetime.timedelta(hours=2)

    # niestandardowy expiry
    delta = datetime.timedelta(minutes=5)
    token2 = sec.create_access_token({"sub": "u2"}, expires_delta=delta)
    data2 = jwt.decode(token2, "testkey123", algorithms=[sec.ALGORITHM])
    exp2 = datetime.datetime.fromtimestamp(data2["exp"], datetime.timezone.utc)
    assert now < exp2 <= now + datetime.timedelta(minutes=6)

def test_totp_secret_and_uri():
    secret = sec.generate_totp_secret()
    # Base32 składa się z A-Z2-7
    assert isinstance(secret, str)
    assert re.fullmatch(r"[A-Z2-7]+", secret)
    uri = sec.get_totp_provisioning_uri("alice@example.com", secret, issuer="VetX")
    # powinno być otpauth:// i secret w query
    assert uri.startswith("otpauth://totp/")
    assert f"secret={secret}" in uri
    assert "issuer=VetX" in uri

def test_generate_qr_code(tmp_path):
    # wygeneruj TOTP URI
    secret = "JBSWY3DPEHPK3PXP"
    uri = pyotp.TOTP(secret).provisioning_uri(name="bob@x.com", issuer_name="VetClinic")
    fn = tmp_path / "qrcode.png"
    # powinno zapisać plik PNG
    sec.generate_qr_code(uri, filename=str(fn))
    assert fn.exists()
    data = fn.read_bytes()
    # sprawdź sygnaturę PNG
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
