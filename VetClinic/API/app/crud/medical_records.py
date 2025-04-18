from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.crud.appointments_crud import get_appointment
from app.crud.animal_crud import get_animal
from app.models.medical_records import MedicalRecord
from app.schemas.medical_records import MedicalRecordCreate, MedicalRecordUpdate

def get_medical_record(db: Session, record_id: int) -> MedicalRecord:
    rec = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found"
        )
    return rec

def get_medical_records(db: Session, skip: int = 0, limit: int = 100) -> list[MedicalRecord]:
    return db.query(MedicalRecord).offset(skip).limit(limit).all()

def create_medical_record(
    db: Session,
    data: MedicalRecordCreate
) -> MedicalRecord:
    get_appointment(db, data.appointment_id)
    get_animal(db, data.animal_id)

    rec = MedicalRecord(
        description=data.description,
        appointment_id=data.appointment_id,
        animal_id=data.animal_id,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec

def update_medical_record(
    db: Session,
    record_id: int,
    rec_update: MedicalRecordUpdate
) -> MedicalRecord:
    db_rec = get_medical_record(db, record_id)

    if "appointment_id" in rec_update.model_fields_set:
        get_appointment(db, rec_update.appointment_id)  
        db_rec.appointment_id = rec_update.appointment_id

    # Jeżeli ustawiono nowe animal_id, zweryfikuj i przypisz
    if "animal_id" in rec_update.model_fields_set:
        get_animal(db, rec_update.animal_id)
        db_rec.animal_id = rec_update.animal_id

    # Dla pozostałych ustawionych w rec_update pól wykonaj setattr
    for field in rec_update.model_fields_set - {"appointment_id", "animal_id"}:
        setattr(db_rec, field, getattr(rec_update, field))

    db.commit()
    db.refresh(db_rec)
    return db_rec

def delete_medical_record(db: Session, record_id: int) -> None:
    db_rec = get_medical_record(db, record_id)
    db.delete(db_rec)
    db.commit()
