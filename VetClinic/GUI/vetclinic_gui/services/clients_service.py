from vetclinic_gui.services.db import SessionLocal
from vetclinic_api.crud.users_crud import (
    get_users, get_user, create_user as crud_create_user,
    update_user as crud_update_user, delete_user as crud_delete_user
)
from vetclinic_api.schemas.users import UserCreate, UserUpdate

class UserService:
    """
    Serwis CRUD dla zasobu użytkowników, korzystający z funkcji w app.crud.user_crud.
    """
    @staticmethod
    def list():
        db = SessionLocal()
        try:
            return get_users(db)
        finally:
            db.close()

    @staticmethod
    def get(user_id: int):
        db = SessionLocal()
        try:
            return get_user(db, user_id)
        finally:
            db.close()

    @staticmethod
    def create(data: dict):
        db = SessionLocal()
        try:
            user_in = UserCreate(**data)
            return crud_create_user(db, user_in)
        finally:
            db.close()

    @staticmethod
    def update(user_id: int, data: dict):
        db = SessionLocal()
        try:
            user_in = UserUpdate(**data)
            return crud_update_user(db, user_id, user_in)
        finally:
            db.close()

    @staticmethod
    def delete(user_id: int):
        db = SessionLocal()
        try:
            return crud_delete_user(db, user_id)
        finally:
            db.close()