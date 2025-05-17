from typing import List
from vetclinic_api.schemas.users import UserOut
from vetclinic_api.crud.users_crud import (
    get_users, get_user,
    create_user as crud_create_user,
    update_user as crud_update_user,
    delete_user as crud_delete_user
)


class ConsultantService:
    @staticmethod
    def list() -> List[UserOut]:
        """Pobiera wszystkich konsultantów (role='consultant')."""
    @staticmethod
    def get(user_id: int) -> UserOut:
        """Szczegóły konsultanta."""
    @staticmethod
    def create(payload: dict) -> UserOut:
        """Tworzy nowego konsultanta."""
    @staticmethod
    def update(user_id: int, payload: dict) -> UserOut:
        """Modyfikuje dane konsultanta."""
    @staticmethod
    def deactivate(user_id: int) -> None:
        """Dezaktywuje konsultanta (lub usuwa)."""
