from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from vetclinic_api.schemas.medical_records import (
    MedicalRecordCreate,
    MedicalRecordResponse,
    MedicalRecordUpdate
)
from vetclinic_api.crud.medical_records import (
    create_medical_record,
    list_medical_records,
    list_medical_records_by_appointment,
    get_medical_record as crud_get_record,
    update_medical_record,
    delete_medical_record
)
from vetclinic_api.core.database import get_db

# Tutaj definiujemy router i prefix
router = APIRouter(
    prefix="/medical_records",
    tags=["Medical Records"]
)

@router.get("/", response_model=List[MedicalRecordResponse])
def read_medical_records(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return list_medical_records(db, skip, limit)

@router.get("/appointment/{appointment_id}", response_model=List[MedicalRecordResponse])
def read_by_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):
    return list_medical_records_by_appointment(db, appointment_id)

@router.get("/{record_id}", response_model=MedicalRecordResponse)
def read_medical_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    try:
        return crud_get_record(db, record_id)
    except HTTPException:
        # jeśli nie ma rekordu — przekaż wyjątek dalej
        raise
    except Exception as e:
        # inne błędy zwracamy 500
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
def create_record(
    record: MedicalRecordCreate,
    db: Session = Depends(get_db)
):
    try:
        return create_medical_record(db, record)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{record_id}", response_model=MedicalRecordResponse)
def update_record(
    record_id: int,
    record: MedicalRecordUpdate,
    db: Session = Depends(get_db)
):
    try:
        return update_medical_record(db, record_id, record)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    try:
        delete_medical_record(db, record_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
