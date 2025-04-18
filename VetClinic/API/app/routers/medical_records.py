from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.medical_records import (
    get_medical_records,
    get_medical_record,
    create_medical_record,
    update_medical_record,
    delete_medical_record,
)
from app.schemas.medical_records import (
    MedicalRecord,
    MedicalRecordCreate,
    MedicalRecordUpdate,
)

router = APIRouter(
    prefix="/medical_records",
    tags=["medical_records"],
)

@router.get("/", response_model=list[MedicalRecord])
def read_records(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return get_medical_records(db, skip=skip, limit=limit)

@router.get("/{record_id}", response_model=MedicalRecord)
def read_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    db_record = get_medical_record(db, record_id)
    if not db_record:
        raise HTTPException(status_code=404, detail="Medical record not found")
    return db_record

@router.post("/", response_model=MedicalRecord, status_code=201)
def create_record(
    record: MedicalRecordCreate,
    db: Session = Depends(get_db),
):
    return create_medical_record(db, record)

@router.put("/{record_id}", response_model=MedicalRecord)
def update_record(
    record_id: int,
    rec_update: MedicalRecordUpdate,
    db: Session = Depends(get_db),
):
    db_record = get_medical_record(db, record_id)
    if not db_record:
        raise HTTPException(status_code=404, detail="Medical record not found")
    return update_medical_record(db, record_id, rec_update)

@router.delete("/{record_id}", status_code=204)
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    db_record = get_medical_record(db, record_id)
    if not db_record:
        raise HTTPException(status_code=404, detail="Medical record not found")
    delete_medical_record(db, record_id)
