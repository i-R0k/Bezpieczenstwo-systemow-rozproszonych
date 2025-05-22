import secrets
from vetclinic_gui.services.db import SessionLocal
from vetclinic_api.crud.users_crud import (
    list_clients,
    get_client,
    create_client as crud_create_user,
    update_client as crud_update_user,
    delete_client as crud_delete_user
)
from vetclinic_api.schemas.users import ClientCreate, UserUpdate

class ClientService:
    """
    Serwis CRUD dla zasobu klientów, korzystający z funkcji w vetclinic_api.crud.users_crud.
    """
    @staticmethod
    def list():
        db = SessionLocal()
        try:
            # Zwracamy pełną listę klientów
            return list_clients(db)
        finally:
            db.close()

    @staticmethod
    def get(client_id: int):
        db = SessionLocal()
        try:
            return get_client(db, client_id)
        finally:
            db.close()

    @staticmethod
    def create(data: dict):
        db = SessionLocal()
        try:
            # uzupełniamy brakujące wymagane pola:
            data = data.copy()
            data.setdefault("password", secrets.token_urlsafe(16))
            data.setdefault("role",     "klient")

            # teraz Pydantic nie będzie protestował
            user_in = ClientCreate(**data)
            return crud_create_user(db, user_in)
        finally:
            db.close()

    @staticmethod
    def update(client_id: int, data: dict):
        db = SessionLocal()
        try:
            user_in = UserUpdate(**data)
            return crud_update_user(db, client_id, user_in)
        finally:
            db.close()

    @staticmethod
    def delete(client_id: int):
        db = SessionLocal()
        try:
            return crud_delete_user(db, client_id)
        finally:
            db.close()
