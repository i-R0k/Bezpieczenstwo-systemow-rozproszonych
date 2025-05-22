# vetclinic_gui/services/consultant_service.py

import requests, secrets
from types import SimpleNamespace
from vetclinic_api.core.config import API_BASE_URL

class ConsultantService:
    @staticmethod
    def list() -> list[SimpleNamespace]:
        """
        Pobiera wszystkich konsultantów z API.
        """
        url = f"{API_BASE_URL}/consultants"
        r = requests.get(url)
        r.raise_for_status()
        return [SimpleNamespace(**item) for item in r.json()]

    @staticmethod
    def create(payload: dict) -> SimpleNamespace:
        """
        Tworzy nowego konsultanta na podstawie payload, w którym
        musi być już wpisany 'backup_email' przez admina.
        Generuje silne hasło, wysyła do API i zwraca:
          - user: SimpleNamespace z danymi
          - raw_password: wygenerowane hasło
          - backup_email: użyty adres
        """
        raw_password = secrets.token_urlsafe(16)
        backup_email = payload.get("backup_email", "").strip()
        if not backup_email:
            raise ValueError("Musisz podać backup_email w payload")

        create_payload = {
            **payload,
            "role":         "consultant",
            "password":     raw_password,
            "backup_email": backup_email,
        }
        url = f"{API_BASE_URL}/consultants"
        resp = requests.post(url, json=create_payload)
        resp.raise_for_status()
        user_data = resp.json()

        user_ns = SimpleNamespace(**user_data)
        return SimpleNamespace(
            user         = user_ns,
            raw_password = raw_password,
            backup_email = backup_email
        )

    @staticmethod
    def update(consultant_id: int, payload: dict) -> SimpleNamespace:
        """
        Aktualizuje istniejącego konsultanta.
        """
        url = f"{API_BASE_URL}/consultants/{consultant_id}"
        r = requests.put(url, json=payload)
        r.raise_for_status()
        return SimpleNamespace(**r.json())

    @staticmethod
    def delete(consultant_id: int) -> None:
        """
        Usuwa konsultanta.
        """
        url = f"{API_BASE_URL}/consultants/{consultant_id}"
        r = requests.delete(url)
        r.raise_for_status()
