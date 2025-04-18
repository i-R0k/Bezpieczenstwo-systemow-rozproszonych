from sqlalchemy.orm import Session
from fastapi import HTTPException, status

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

def create_medical_record(db: Session, record_in: MedicalRecordCreate) -> MedicalRecord:
    db_rec = MedicalRecord(**record_in.dict())
    db.add(db_rec)
    db.commit()
    db.refresh(db_rec)
    return db_rec

def update_medical_record(db: Session, record_id: int, rec_update: MedicalRecordUpdate) -> MedicalRecord:
    db_rec = get_medical_record(db, record_id)
    for field, value in rec_update.dict(exclude_unset=True).items():
        setattr(db_rec, field, value)
    db.commit()
    db.refresh(db_rec)
    return db_rec

def delete_medical_record(db: Session, record_id: int) -> None:
    db_rec = get_medical_record(db, record_id)
    db.delete(db_rec)
    db.commit()
