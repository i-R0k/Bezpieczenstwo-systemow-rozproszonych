from sqlalchemy.orm import Session
from passlib.context import CryptContext

from vetclinic_api.models.users import Doctor
from vetclinic_api.schemas.users import DoctorCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_doctor(db: Session, doctor_in: DoctorCreate) -> Doctor:
    """
    Tworzy nowego lekarza.
    """
    hashed = get_password_hash(doctor_in.password)
    doctor = Doctor(
        first_name   = doctor_in.first_name,
        last_name    = doctor_in.last_name,
        email        = doctor_in.email,
        password_hash= hashed,
        specialization= doctor_in.specialization,
        permit_number = doctor_in.permit_number,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor

def list_doctors(db: Session) -> list[Doctor]:
    """
    Zwraca listę wszystkich lekarzy.
    """
    return db.query(Doctor).all()

def get_doctor(db: Session, doctor_id: int) -> Doctor | None:
    """
    Pobiera lekarza po ID.
    """
    return db.query(Doctor).get(doctor_id)

def update_doctor(db: Session, doctor_id: int, data_in: UserUpdate) -> Doctor | None:
    """
    Aktualizuje dane lekarza. Hashuje nowe hasło, jeśli podano.
    """
    doctor = get_doctor(db, doctor_id)
    if not doctor:
        return None
    data = data_in.model_dump(exclude_unset=True)
    if "password" in data:
        data["password_hash"] = get_password_hash(data.pop("password"))
    for field, value in data.items():
        setattr(doctor, field, value)
    db.commit()
    db.refresh(doctor)
    return doctor

def delete_doctor(db: Session, doctor_id: int) -> bool:
    """
    Usuwa lekarza. Zwraca True, jeśli usunięto.
    """
    doctor = get_doctor(db, doctor_id)
    if not doctor:
        return False
    db.delete(doctor)
    db.commit()
    return True
