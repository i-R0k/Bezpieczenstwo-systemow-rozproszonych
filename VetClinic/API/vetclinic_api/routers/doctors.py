from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from vetclinic_api.core.database import get_db
from vetclinic_api.crud.doctors import (
    create_doctor, list_doctors, get_doctor,
    update_doctor, delete_doctor
)
from vetclinic_api.models.users import Doctor
from vetclinic_api.schemas.users import DoctorCreate, DoctorOut, UserUpdate

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.get("/", response_model=List[DoctorOut])
def read_doctors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    docs = list_doctors(db)
    return docs[skip : skip + limit]


@router.post("/", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor_endpoint(data: DoctorCreate, db: Session = Depends(get_db)):
    # 1) normalizacja
    first = data.first_name.strip().lower()
    last  = data.last_name.strip().lower()

    # 2) generowanie unikatowego emaila
    base  = f"{first[0]}.{last}"
    email = f"{base}@lekarz.vetclinic.com"
    if db.query(Doctor).filter_by(email=email).first():
        base = f"{first[0]}{last}"
        email = f"{base}@lekarz.vetclinic.com"
        if db.query(Doctor).filter_by(email=email).first():
            i = 2
            while i <= len(first):
                prefix = first[:i]
                tmp    = f"{prefix}{last}@lekarz.vetclinic.com"
                if not db.query(Doctor).filter_by(email=tmp).first():
                    email = tmp
                    break
                i += 1
            else:
                # ostateczny suffix
                suffix = 1
                base0  = f"{first[0]}{last}"
                while True:
                    tmp = f"{base0}{suffix}@lekarz.vetclinic.com"
                    if not db.query(Doctor).filter_by(email=tmp).first():
                        email = tmp
                        break
                    suffix += 1

    # 3) podmień w danych
    data_dict = data.model_dump()
    data_dict["email"] = email

    # 4) wywołaj CRUD (który sam wygeneruje hasło i wyśle je na backup_email)
    raw_password, doctor = create_doctor(db, DoctorCreate(**data_dict))

    # 5) zwróć od razu utworzony obiekt
    return doctor


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
