import requests

API_BASE_URL = "http://127.0.0.1:8000"  # Adres lokalnego serwera FastAPI

def get_animals():
    response = requests.get(f"{API_BASE_URL}/animals/")
    response.raise_for_status()
    return response.json()  # Zakładamy, że API zwraca listę słowników

def create_animal(animal_data):
    # animal_data to np. słownik zawierający: name, species, owner_id, itd.
    response = requests.post(f"{API_BASE_URL}/animals/", json=animal_data)
    response.raise_for_status()
    return response.json()

def update_animal(animal_id, animal_data):
    response = requests.put(f"{API_BASE_URL}/animals/{animal_id}", json=animal_data)
    response.raise_for_status()
    return response.json()

def delete_animal(animal_id):
    response = requests.delete(f"{API_BASE_URL}/animals/{animal_id}")
    response.raise_for_status()
    return response.json()
