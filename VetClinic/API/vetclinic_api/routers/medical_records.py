from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from vetclinic_api.schemas.medical_records import (
    MedicalRecordCreate,
    MedicalRecordUpdate,
    MedicalRecord
)
from vetclinic_api.core.database import get_db
from vetclinic_api.crud.medical_records import (
    list_medical_records,
    list_medical_records_by_appointment,
    get_medical_record,
    create_medical_record,
    update_medical_record,
    delete_medical_record
)

router = APIRouter(
    prefix="/medical_records",
    tags=["medical_records"]
)

@router.get("/", response_model=List[MedicalRecord])
def read_medical_records(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return list_medical_records(db, skip=skip, limit=limit)

@router.get("/appointment/{appointment_id}", response_model=List[MedicalRecord])
def read_by_appointment(appointment_id: int, db: Session = Depends(get_db)):
    return list_medical_records_by_appointment(db, appointment_id)

@router.get("/{record_id}", response_model=MedicalRecord)
def read_medical_record(record_id: int, db: Session = Depends(get_db)):
    return get_medical_record(db, record_id)

@router.post("/", response_model=MedicalRecord, status_code=status.HTTP_201_CREATED)
def post_medical_record(record: MedicalRecordCreate, db: Session = Depends(get_db)):
    return create_medical_record(db, record)

@router.put("/{record_id}", response_model=MedicalRecord)
def put_medical_record(record_id: int, record: MedicalRecordUpdate, db: Session = Depends(get_db)):
    return update_medical_record(db, record_id, record)

@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_medical_record(record_id: int, db: Session = Depends(get_db)):
    delete_medical_record(db, record_id)
