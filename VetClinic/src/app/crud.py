"""
Funkcje CRUD – operacje na bazie danych, oddzielone od logiki endpointów.
"""

from sqlalchemy.orm import Session
from ..app import models, schemas

def create_user(db: Session, user: schemas.UserCreate):
    # Przykładowa funkcja tworząca użytkownika
    fake_hashed_password = "hashed_" + user.password  # W rzeczywistości użyj funkcji haszującej
    db_user = models.User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        password_hash=fake_hashed_password,
        role="owner"  # Przykładowa rola – można modyfikować
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
