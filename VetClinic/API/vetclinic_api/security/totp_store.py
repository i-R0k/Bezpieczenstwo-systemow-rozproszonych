from __future__ import annotations

from threading import Lock

from vetclinic_api.security.totp import generate_totp_secret, provisioning_uri


class InMemoryTotpDemoStore:
    def __init__(self) -> None:
        self._secrets: dict[str, str] = {}
        self._lock = Lock()

    def create_secret(self, account_name: str) -> dict:
        secret = generate_totp_secret()
        with self._lock:
            self._secrets[account_name] = secret
        return {
            "account_name": account_name,
            "secret": secret,
            "provisioning_uri": provisioning_uri(secret, account_name),
        }

    def get_secret(self, account_name: str) -> str:
        with self._lock:
            if account_name not in self._secrets:
                raise KeyError(f"TOTP secret for account {account_name!r} not found")
            return self._secrets[account_name]

    def clear(self) -> None:
        with self._lock:
            self._secrets.clear()


TOTP_DEMO_STORE = InMemoryTotpDemoStore()
