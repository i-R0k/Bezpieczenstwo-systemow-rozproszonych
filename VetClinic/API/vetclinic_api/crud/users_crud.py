from sqlalchemy.orm import Session
from vetclinic_api.schemas.users import UserCreate, UserUpdate
from vetclinic_api.models.users import Client, Doctor, Consultant
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_user(db: Session, user: UserCreate):
    """Tworzy nowego użytkownika w zależności od roli."""
    hashed_password = get_password_hash(user.password)
    if user.role == "klient":
        new_user = Client(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            password_hash=hashed_password,
            phone_number=user.phone_number,
            address=user.address,
            postal_code=user.postal_code
        )
    elif user.role == "lekarz":
        new_user = Doctor(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            password_hash=hashed_password,
            specialization=user.specialization,
            permit_number=user.permit_number
        )
    elif user.role == "konsultant":
        new_user = Consultant(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            password_hash=hashed_password
        )
    else:
        raise ValueError("Nieprawidłowa rola użytkownika")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_users(db: Session):
    """Pobiera wszystkich użytkowników (klienci, lekarze, konsultanci)."""
    users = []
    users.extend(db.query(Client).all())
    users.extend(db.query(Doctor).all())
    users.extend(db.query(Consultant).all())
    return users

def get_user(db: Session, user_id: int):
    """Pobiera użytkownika o podanym ID, niezależnie od jego roli."""
    user = db.query(Client).get(user_id)
    if user:
        return user
    user = db.query(Doctor).get(user_id)
    if user:
        return user
    return db.query(Consultant).get(user_id)

def update_user(db: Session, user_id: int, user_in: UserUpdate):
    """
    Aktualizuje istniejącego użytkownika.
    Jeśli w user_in podano nowe hasło, zostanie ono ponownie zahashowane.
    """
    user = get_user(db, user_id)
    if not user:
        return None
    data = user_in.model_dump(exclude_unset=True)
    if "password" in data:
        data["password_hash"] = get_password_hash(data.pop("password"))
    for field, value in data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    """Usuwa użytkownika o podanym ID i zwraca True/False czy operacja się powiodła."""
    user = get_user(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True
