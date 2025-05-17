import requests
from types import SimpleNamespace
from vetclinic_api.core.config import API_BASE_URL

class ConsultantService:
    @staticmethod
    def list() -> list:
        url = f"{API_BASE_URL}/consultants"
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        return [SimpleNamespace(**item) for item in data]

    @staticmethod
    def create(payload: dict) -> SimpleNamespace:
        url = f"{API_BASE_URL}/consultants"
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        return SimpleNamespace(**resp.json())

    @staticmethod
    def update(consultant_id: int, payload: dict) -> SimpleNamespace:
        url = f"{API_BASE_URL}/consultants/{consultant_id}"
        resp = requests.put(url, json=payload)
        resp.raise_for_status()
        return SimpleNamespace(**resp.json())

    @staticmethod
    def delete(consultant_id: int) -> None:
        url = f"{API_BASE_URL}/consultants/{consultant_id}"
        resp = requests.delete(url)
        resp.raise_for_status()
