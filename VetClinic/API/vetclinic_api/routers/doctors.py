from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from vetclinic_api.core.database import get_db
from vetclinic_api.crud.doctors import (
    create_doctor, list_doctors, get_doctor,
    update_doctor, delete_doctor
)
from vetclinic_api.schemas.users import DoctorCreate, DoctorOut, UserUpdate

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.get("/", response_model=List[DoctorOut])
def read_doctors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    docs = list_doctors(db)
    return docs[skip : skip + limit]


@router.post("/", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor_endpoint(user: DoctorCreate, db: Session = Depends(get_db)):
    return create_doctor(db, user)


@router.get("/{doctor_id}", response_model=DoctorOut)
def read_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doc = get_doctor(db, doctor_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor not found")
    return doc


@router.put("/{doctor_id}", response_model=DoctorOut)
def update_doctor_endpoint(doctor_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    doc = update_doctor(db, doctor_id, data)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor not found")
    return doc


@router.delete("/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_doctor_endpoint(doctor_id: int, db: Session = Depends(get_db)):
    ok = delete_doctor(db, doctor_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor not found")
