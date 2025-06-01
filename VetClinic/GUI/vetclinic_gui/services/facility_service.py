import requests
from types import SimpleNamespace
from vetclinic_api.core.config import API_BASE_URL

class FacilityService:
    """
    Serwis HTTP CRUD dla zasobu placówek (facilities).
    """

    @staticmethod
    def list() -> list[SimpleNamespace]:
        """
        Pobiera listę wszystkich placówek.
        GET /facilities
        """
        url = f"{API_BASE_URL}/facilities"
        try:
            r = requests.get(url)
            r.raise_for_status()
            # oczekujemy listy JSON-ów, każdy zamieniamy na SimpleNamespace
            return [SimpleNamespace(**fac) for fac in r.json()]
        except requests.RequestException:
            return []

    @staticmethod
    def get(facility_id: int) -> SimpleNamespace | None:
        """
        Pobiera jedną placówkę po ID.
        GET /facilities/{facility_id}
        """
        url = f"{API_BASE_URL}/facilities/{facility_id}"
        try:
            r = requests.get(url)
            r.raise_for_status()
            return SimpleNamespace(**r.json())
        except requests.RequestException:
            return None

    @staticmethod
    def create(data: dict) -> SimpleNamespace:
        """
        Tworzy nową placówkę.
        POST /facilities
        """
        url = f"{API_BASE_URL}/facilities"
        r = requests.post(url, json=data)
        r.raise_for_status()
        # zwróci FacilityRead jako JSON
        return SimpleNamespace(**r.json())

    @staticmethod
    def update(facility_id: int, payload: dict) -> SimpleNamespace:
        """
        Modyfikuje istniejącą placówkę.
        PUT /facilities/{facility_id}
        """
        url = f"{API_BASE_URL}/facilities/{facility_id}"
        r = requests.put(url, json=payload)
        r.raise_for_status()
        return SimpleNamespace(**r.json())

    @staticmethod
    def delete(facility_id: int) -> None:
        """
        Usuwa placówkę.
        DELETE /facilities/{facility_id}
        """
        url = f"{API_BASE_URL}/facilities/{facility_id}"
        r = requests.delete(url)
        r.raise_for_status()
        # nie zwracamy treści, samo wywołanie bez wyjątku = sukces
