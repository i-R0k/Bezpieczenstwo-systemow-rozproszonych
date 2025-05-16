import requests
from types import SimpleNamespace
from vetclinic_api.core.config import API_BASE_URL

class DoctorService:
    """
    Serwis do pobierania listy lekarzy z API.
    """
    @staticmethod
    def list():
        """
        Pobiera listę lekarzy z endpointu /doctors.
        Zwraca listę obiektów z atrybutami odpowiadającymi polom JSON.
        """
        url = f"{API_BASE_URL}/doctors"
        try:
            response = requests.get(url)
            response.raise_for_status()
            doctors_data = response.json()
            # Konwersja dict na obiekt z atrybutami
            return [SimpleNamespace(**doc) for doc in doctors_data]
        except requests.RequestException as e:
            # W razie błędu zwracamy pustą listę lub można logować wyjątek
            return []
