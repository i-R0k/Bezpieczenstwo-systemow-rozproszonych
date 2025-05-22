from sqlalchemy.orm import Session
from passlib.context import CryptContext
import secrets

from vetclinic_api.models.users import Doctor
from vetclinic_api.schemas.users import DoctorCreate, UserUpdate
from vetclinic_api.services.email_service import EmailService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_doctor(db: Session, doc_in: DoctorCreate) -> Doctor:
    """
    Tworzy nowego lekarza:
     - generuje losowe hasło,
     - hashuje je,
     - ustawia must_change_password=True,
     - zapisuje backup_email,
     - wysyła mail z tymczasowym hasłem.
    """
    raw_password = secrets.token_urlsafe(16)
    hashed       = get_password_hash(raw_password)

    doctor = Doctor(
        first_name           = doc_in.first_name,
        last_name            = doc_in.last_name,
        email                = doc_in.email,
        password_hash        = hashed,
        specialization       = doc_in.specialization,
        permit_number        = doc_in.permit_number,
        backup_email         = doc_in.backup_email,
        must_change_password = True,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    # wyślij tymczasowe hasło
    EmailService.send_temporary_password(doctor.backup_email, raw_password)
    return doctor

def list_doctors(db: Session) -> list[Doctor]:
    return db.query(Doctor).all()

def get_doctor(db: Session, doctor_id: int) -> Doctor | None:
    return db.get(Doctor, doctor_id)

def update_doctor(db: Session, doctor_id: int, data_in: UserUpdate) -> Doctor | None:
    """
    Aktualizuje lekarza. Jeżeli podano nowe 'password', to:
      - hashujemy je,
      - ustawiamy must_change_password=True.
    Aktualizujemy też backup_email, specialization i permit_number.
    """
    doctor = get_doctor(db, doctor_id)
    if not doctor:
        return None

    data = data_in.model_dump(exclude_unset=True)
    if "password" in data:
        raw_pw = data.pop("password")
        doctor.password_hash = get_password_hash(raw_pw)
        doctor.must_change_password = True

    if "backup_email" in data:
        doctor.backup_email = data["backup_email"]

    if "specialization" in data:
        doctor.specialization = data["specialization"]

    if "permit_number" in data:
        doctor.permit_number = data["permit_number"]

    # możesz też zaktualizować email, first_name, last_name...
    for attr in ("first_name","last_name","email"):
        if attr in data:
            setattr(doctor, attr, data[attr])

    db.commit()
    db.refresh(doctor)
    return doctor

def delete_doctor(db: Session, doctor_id: int) -> bool:
    doctor = get_doctor(db, doctor_id)
    if not doctor:
        return False
    db.delete(doctor)
    db.commit()
    return True
