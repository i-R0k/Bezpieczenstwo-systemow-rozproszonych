from sqlalchemy.orm import Session
from app.schemas import users
from app.models.users import Client, Doctor, Consultant
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_user(db: Session, user: users.UserCreate):
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
