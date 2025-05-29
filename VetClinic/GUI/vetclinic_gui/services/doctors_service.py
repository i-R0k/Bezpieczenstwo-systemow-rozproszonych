import requests
from types import SimpleNamespace
from vetclinic_api.core.config import API_BASE_URL

class DoctorService:
    @staticmethod
    def list():
        url = f"{API_BASE_URL}/doctors"
        try:
            r = requests.get(url)
            r.raise_for_status()
            return [SimpleNamespace(**doc) for doc in r.json()]
        except requests.RequestException:
            return []

    @staticmethod
    def get(doctor_id):
        url = f"{API_BASE_URL}/doctors/{doctor_id}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return SimpleNamespace(**response.json())
        except requests.RequestException:
            return None

    @staticmethod
    def create(data: dict):
        url = f"{API_BASE_URL}/doctors"
        r = requests.post(url, json=data)
        r.raise_for_status()
        # tu dostajemy od razu obiekt lekarza
        return SimpleNamespace(**r.json())

    @staticmethod
    def update(doctor_id, payload):
        url = f"{API_BASE_URL}/doctors/{doctor_id}"
        try:
            response = requests.put(url, json=payload)
            response.raise_for_status()
            return SimpleNamespace(**response.json())
        except requests.RequestException as e:
            raise Exception("Błąd aktualizacji lekarza: " + str(e))

    @staticmethod
    def delete(doctor_id):
        url = f"{API_BASE_URL}/doctors/{doctor_id}"
        try:
            response = requests.delete(url)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception("Błąd usuwania lekarza: " + str(e))
