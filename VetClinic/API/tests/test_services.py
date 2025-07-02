import pytest
import os
import logging
import json
from unittest.mock import patch, MagicMock
from vetclinic_api.services.email_service import EmailService
from vetclinic_api.crud.invoice_crud import get_invoice

import vetclinic_api.services.payment_service as payment_service
import vetclinic_api.services.payu_service as payu_service

# EMAIL SERVICE

def test_send_temporary_password(monkeypatch):
    # Mock smtplib.SMTP_SSL, żeby nie wysyłać prawdziwych maili!
    class DummySMTP:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def set_debuglevel(self, level): self.debug = level
        def login(self, user, pwd): self.logged = (user, pwd)
        def send_message(self, msg): self.sent = msg

    monkeypatch.setattr("smtplib.SMTP_SSL", lambda *a, **k: DummySMTP())
    # Nic nie powinno rzucić wyjątku
    EmailService.send_temporary_password("test@email.com", "12345")

# PAYMENT SERVICE

def test_create_stripe_session(monkeypatch):
    class DummySession:
        id = "sess123"
    # Patchujemy stripe.checkout.Session.create
    monkeypatch.setattr(payment_service.stripe.checkout.Session, "create", lambda *a, **k: DummySession())
    session = payment_service.create_stripe_session(10, 20.5)
    assert session.id == "sess123"

# PAYU SERVICE

def test_get_access_token_success(monkeypatch):
    class DummyResp:
        def __init__(self): self.status_code=200; self.headers={"Content-Type":"application/json"}; self.text='{"access_token":"tok"}'
        def json(self): return {"access_token":"tok"}
        def raise_for_status(self): pass
    monkeypatch.setattr(payu_service.requests, "post", lambda *a, **k: DummyResp())
    token = payu_service._get_access_token()
    assert token == "tok"

def test_get_access_token_fail(monkeypatch):
    class DummyResp:
        def __init__(self): self.status_code=200; self.headers={"Content-Type":"text/plain"}; self.text="fail"
        def raise_for_status(self): pass
        def json(self): raise ValueError()
    monkeypatch.setattr(payu_service.requests, "post", lambda *a, **k: DummyResp())
    with pytest.raises(RuntimeError):
        payu_service._get_access_token()

def test_create_payu_order_json(monkeypatch):
    class DummyResp:
        def __init__(self): self.status_code=200; self.headers={"Content-Type":"application/json"}; self.text='{"res":1}'
        def raise_for_status(self): pass
        def json(self): return {"res":1}
    monkeypatch.setattr(payu_service, "_get_access_token", lambda: "tok")
    monkeypatch.setattr(payu_service.requests, "post", lambda *a, **k: DummyResp())
    res = payu_service.create_payu_order(1, 99.9, "b@x", "John Doe")
    assert res == {"res":1}

def test_create_payu_order_redirect(monkeypatch):
    class DummyResp:
        def __init__(self):
            self.status_code=302
            self.headers={"Content-Type":"application/json", "Location":"https://payu/redirect?orderId=123"}
            self.text=""
        def raise_for_status(self): pass
    monkeypatch.setattr(payu_service, "_get_access_token", lambda: "tok")
    monkeypatch.setattr(payu_service.requests, "post", lambda *a, **k: DummyResp())
    res = payu_service.create_payu_order(1, 99.9, "b@x", "John Doe")
    assert res["orderId"] == "123"
    assert "redirectUri" in res

def test_create_payu_order_fail(monkeypatch):
    class DummyResp:
        def __init__(self): self.status_code=200; self.headers={"Content-Type":"text/plain"}; self.text="fail"
        def raise_for_status(self): pass
        def json(self): raise ValueError()
    monkeypatch.setattr(payu_service, "_get_access_token", lambda: "tok")
    monkeypatch.setattr(payu_service.requests, "post", lambda *a, **k: DummyResp())
    with pytest.raises(RuntimeError):
        payu_service.create_payu_order(1, 1, "b@x", "Jan Nowak")

