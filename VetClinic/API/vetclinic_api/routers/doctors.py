from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from vetclinic_api.core.database import get_db
from vetclinic_api.crud.users_crud import get_users, get_user
from vetclinic_api.crud.appointments_crud import get_appointments
from vetclinic_api.schemas.users import UserOut
from vetclinic_api.schemas.appointment import Appointment

router = APIRouter(prefix="/doctors", tags=["doctors"])

@router.get("/", response_model=List[UserOut])
def list_doctors(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Zwraca listę wszystkich aktywnych lekarzy (role='lekarz'),
    z paginacją skip/limit.
    """
    all_users = get_users(db)                  # pobieramy wszystkich użytkowników
    doctors = [u for u in all_users if u.role == "lekarz"]
    return doctors[skip : skip + limit]

@router.get("/{doctor_id}", response_model=UserOut)
def read_doctor(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    """
    Zwraca dane konkretnego lekarza lub 404, jeśli nie istnieje.
    """
    user = get_user(db, doctor_id)
    if not user or user.role != "lekarz":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor not found")
    return user

@router.get("/{doctor_id}/appointments", response_model=List[Appointment])
def get_doctor_appointments(
    doctor_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Zwraca listę wizyt przypisanych do lekarza (można potem
    po stronie klienta podzielić na przeszłe, bieżące i przyszłe).
    """
    user = get_user(db, doctor_id)
    if not user or user.role != "lekarz":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Doctor not found")

    all_apps = get_appointments(db)
    doctor_apps = [a for a in all_apps if a.doctor_id == doctor_id]
    return doctor_apps[skip : skip + limit]
