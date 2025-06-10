from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from vetclinic_api.crud.appointments_crud import get_appointment
from vetclinic_api.crud.animal_crud import get_animal
from vetclinic_api.models.medical_records import MedicalRecord as MRModel
from vetclinic_api.schemas.medical_records import MedicalRecordCreate, MedicalRecordUpdate
from vetclinic_api.crud import blockchain_crud
from vetclinic_api.core.blockchain import BlockchainProvider

import hashlib
import json

provider = BlockchainProvider()

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

def get_records_by_owner(owner: str):
    contract, _, _ = provider.get()
    ids = contract.functions.getRecordsByOwner(owner).call()
    return ids


def _compute_hash_and_payload(db_record: MRModel) -> Dict[str, Any]:
    """Helper: buduje dict z polami rekordu + created_at, zamienia na JSON + hash."""
    record_dict = {
        "id": db_record.id,
        "appointment_id": db_record.appointment_id,
        "animal_id": db_record.animal_id,
        "description": db_record.description,
        "diagnosis": db_record.diagnosis,
        "treatment": db_record.treatment,
        "created_at": db_record.created_at.isoformat(),
    }
    json_str = json.dumps(record_dict, sort_keys=True)
    data_hash = hashlib.sha256(json_str.encode()).hexdigest()
    return {"record_dict": record_dict, "data_hash": data_hash}


def create_medical_record(
    db: Session,
    data: MedicalRecordCreate
) -> Dict[str, Any]:
    # Walidacje kluczy obcych
    get_appointment(db, data.appointment_id)
    get_animal(db, data.animal_id)

    # 1) Zapis do DB
    db_record = MRModel(
        description=data.description,
        appointment_id=data.appointment_id,
        animal_id=data.animal_id,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    # 2) Hash + payload
    payload = _compute_hash_and_payload(db_record)

    # 3) Zapis na blockchainie
    tx_hash = blockchain_crud.add_record(db_record.id, payload["data_hash"])

    # 4) Zwrócenie pełnych danych
    return {
        **payload["record_dict"],
        "data_hash": payload["data_hash"],
        "blockchain_tx": tx_hash
    }


def update_medical_record(
    db: Session,
    record_id: int,
    rec_update: MedicalRecordUpdate
) -> Dict[str, Any]:
    db_rec = get_medical_record(db, record_id)

    # Aktualizujemy pola w DB
    if rec_update.appointment_id is not None:
        get_appointment(db, rec_update.appointment_id)
        db_rec.appointment_id = rec_update.appointment_id
    if rec_update.animal_id is not None:
        get_animal(db, rec_update.animal_id)
        db_rec.animal_id = rec_update.animal_id
    if rec_update.description is not None:
        db_rec.description = rec_update.description

    db.commit()
    db.refresh(db_rec)

    # Nowy hash + payload
    payload = _compute_hash_and_payload(db_rec)

    # Aktualizacja on-chain
    tx_hash = blockchain_crud.update_record(db_rec.id, payload["data_hash"])

    return {
        **payload["record_dict"],
        "data_hash": payload["data_hash"],
        "blockchain_tx": tx_hash
    }


def delete_medical_record(db: Session, record_id: int) -> str:
    # 1) Oznacz rekord jako usunięty on-chain
    #    (wymaga, aby kontrakt miał funkcję deleteRecord)
    tx_hash = blockchain_crud.delete_record(record_id)

    # 2) Usuń z DB
    db_rec = get_medical_record(db, record_id)
    db.delete(db_rec)
    db.commit()

    return tx_hash
