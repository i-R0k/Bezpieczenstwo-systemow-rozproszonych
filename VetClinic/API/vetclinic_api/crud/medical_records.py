from typing import List, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from vetclinic_api.crud.appointments_crud import get_appointment
from vetclinic_api.crud.animal_crud import get_animal
from vetclinic_api.models.medical_records import MedicalRecord as MRModel
from vetclinic_api.schemas.medical_records import MedicalRecordCreate, MedicalRecordUpdate, MedicalRecordResponse
from vetclinic_api.crud.blockchain_crud import (
    add_record as bc_add_record,
    update_record as bc_update_record,
    delete_record as bc_delete_record
)

import hashlib
import json


def list_medical_records(db: Session, skip: int = 0, limit: int = 100) -> List[MRModel]:
    return db.query(MRModel).offset(skip).limit(limit).all()


def list_medical_records_by_appointment(db: Session, appointment_id: int) -> List[MRModel]:
    return (
        db.query(MRModel)
          .filter(MRModel.appointment_id == appointment_id)
          .all()
    )


def get_medical_record(db: Session, record_id: int) -> MRModel:
    rec = db.query(MRModel).filter(MRModel.id == record_id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found"
        )
    return rec


def create_medical_record(db: Session, data: MedicalRecordCreate) -> MedicalRecordResponse:
    # Validate related entities
    get_appointment(db, data.appointment_id)
    get_animal(db, data.animal_id)

    # Persist to DB
    rec = MRModel(
        appointment_id=data.appointment_id,
        animal_id=data.animal_id,
        description=data.description,
        diagnosis=data.diagnosis,
        treatment=data.treatment,
        notes=data.notes,
        visit_date=data.visit_date
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    # Prepare record for hashing
    record_dict = {
        "id": rec.id,
        **data.dict(),
        "created_at": rec.created_at.isoformat()
    }
    json_str = json.dumps(record_dict, sort_keys=True)
    data_hash = hashlib.sha256(json_str.encode()).hexdigest()

    # Write to blockchain
    tx_hash = bc_add_record(rec.id, data_hash)

    # Return combined result
    return MedicalRecordResponse(
        id=rec.id,
        appointment_id=rec.appointment_id,
        animal_id=rec.animal_id,
        description=rec.description,
        diagnosis=rec.diagnosis,
        treatment=rec.treatment,
        notes=rec.notes,
        visit_date=rec.visit_date,
        created_at=rec.created_at,
        data_hash=data_hash,
        blockchain_tx=tx_hash
    )


def update_medical_record(db: Session, record_id: int, data: MedicalRecordUpdate) -> MedicalRecordResponse:
    db_rec = get_medical_record(db, record_id)

    # Validate and update DB fields
    if data.appointment_id is not None:
        get_appointment(db, data.appointment_id)
        db_rec.appointment_id = data.appointment_id
    if data.animal_id is not None:
        get_animal(db, data.animal_id)
        db_rec.animal_id = data.animal_id

    # Update other fields
    for field, value in data.dict(exclude_unset=True).items():
        setattr(db_rec, field, value)

    db.commit()
    db.refresh(db_rec)

    # Re-hash updated record
    record_dict = {
        "id": db_rec.id,
        **{k: (getattr(db_rec, k).isoformat() if hasattr(getattr(db_rec, k), 'isoformat') else getattr(db_rec, k)) for k in [
            "appointment_id", "animal_id", "description", "diagnosis", "treatment", "notes", "visit_date"
        ]},
        "created_at": db_rec.created_at.isoformat()
    }
    json_str = json.dumps(record_dict, sort_keys=True)
    new_hash = hashlib.sha256(json_str.encode()).hexdigest()

    # Update on blockchain
    tx_hash = bc_update_record(db_rec.id, new_hash)

    return MedicalRecordResponse(
        id=db_rec.id,
        appointment_id=db_rec.appointment_id,
        animal_id=db_rec.animal_id,
        description=db_rec.description,
        diagnosis=db_rec.diagnosis,
        treatment=db_rec.treatment,
        notes=db_rec.notes,
        visit_date=db_rec.visit_date,
        created_at=db_rec.created_at,
        data_hash=new_hash,
        blockchain_tx=tx_hash
    )


def delete_medical_record(db: Session, record_id: int) -> dict:
    # Remove from DB
    db_rec = get_medical_record(db, record_id)
    db.delete(db_rec)
    db.commit()

    # Mark as deleted on blockchain
    tx_hash = bc_delete_record(record_id)

    return {"status": "deleted", "tx_hash": tx_hash}

