from __future__ import annotations

import pyotp


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(secret: str, account_name: str, issuer_name: str = "BSR-BFT-Demo") -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=account_name, issuer_name=issuer_name)


def verify_totp_code(secret: str, code: str, valid_window: int = 1) -> bool:
    if not secret or not code:
        return False
    return bool(pyotp.TOTP(secret).verify(code, valid_window=valid_window))
