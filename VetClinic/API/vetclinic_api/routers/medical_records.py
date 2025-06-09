from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from vetclinic_api.core.database import get_db
from vetclinic_api.schemas.medical_records import MedicalRecord, MedicalRecordCreate, MedicalRecordUpdate
from vetclinic_api.crud.medical_records import (
    get_medical_record,
    get_medical_records,
    create_medical_record,
    update_medical_record,
    delete_medical_record,
)

router = APIRouter(prefix="/medical_records", tags=["medical_records"])

@router.post("/", response_model=MedicalRecord, status_code=status.HTTP_201_CREATED)
def create_record(record_in: MedicalRecordCreate, db: Session = Depends(get_db)):
    return create_medical_record(db, record_in)

@router.get("/", response_model=list[MedicalRecord])
def list_records(skip: int=0, limit: int=100, db: Session = Depends(get_db)):
    return get_medical_records(db, skip, limit)

@router.get("/{record_id}", response_model=MedicalRecord)
def get_record(record_id: int, db: Session = Depends(get_db)):
    return get_medical_record(db, record_id)

@router.put("/{record_id}", response_model=MedicalRecord)
def put_record(record_id: int, record_in: MedicalRecordUpdate, db: Session = Depends(get_db)):
    return update_medical_record(db, record_id, record_in)

@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def del_record(record_id: int, db: Session = Depends(get_db)):
    delete_medical_record(db, record_id)
