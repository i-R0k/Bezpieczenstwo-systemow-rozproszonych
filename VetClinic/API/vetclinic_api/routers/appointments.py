# VetClinic/API/vetclinic_api/routers/appointments.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime, time, timedelta

from vetclinic_api.schemas.appointment import Appointment, AppointmentCreate, AppointmentUpdate
from vetclinic_api.crud import appointments_crud
from vetclinic_api.core.database import get_db
from vetclinic_api.models.appointments import Appointment as AppointmentModel

router = APIRouter(
    prefix="/appointments",
    tags=["appointments"]
)

@router.post("/", response_model=Appointment, status_code=status.HTTP_201_CREATED)
def create_appointment(appointment: AppointmentCreate, db: Session = Depends(get_db)):
    return appointments_crud.create_appointment(db, appointment)

@router.get("/", response_model=List[Appointment])
def read_appointments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return appointments_crud.get_appointments(db, skip=skip, limit=limit)

@router.get("/{appointment_id}", response_model=Appointment)
def read_appointment(appointment_id: int, db: Session = Depends(get_db)):
    db_appointment = appointments_crud.get_appointment(db, appointment_id)
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return db_appointment

@router.put("/{appointment_id}", response_model=Appointment)
def update_appointment(appointment_id: int, appointment: AppointmentUpdate, db: Session = Depends(get_db)):
    db_appointment = appointments_crud.update_appointment(db, appointment_id, appointment)
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return db_appointment

@router.delete("/{appointment_id}", response_model=Appointment)
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    db_appointment = appointments_crud.delete_appointment(db, appointment_id)
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return db_appointment

@router.get(
    "/free_slots/",
    response_model=List[str],
    summary="Zwraca wolne kwadransowe sloty (HH:MM) dla lekarza w zadanym dniu"
)
def get_free_slots(
    doctor_id: int = Query(..., description="ID lekarza"),
    date: date = Query(..., description="Data wizyty w formacie YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    1. Jeśli dzień tygodnia to niedziela (weekday()==6), zwraca [].
    2. Generuje wszystkie kwadransy od 08:00 do 18:45.
    3. Pobiera z bazy wszystkie istniejące wizyty (Appointment) dla doctor_id w tym dniu.
    4. Filtruje out te godziny (HH:MM), które są już zajęte.
    5. Zwraca posortowaną listę wolnych godzin jako ["HH:MM", ...].
    """
    # 1) Jeżeli niedziela (weekday == 6), lekarz nie przyjmuje
    if date.weekday() == 6:
        return []

    # 2) Generujemy wszystkie możliwe kwadransy od 08:00 do 18:45
    all_slots: List[str] = []
    current = datetime.combine(date, time(hour=8, minute=0))
    end_slot = datetime.combine(date, time(hour=18, minute=45))
    while current <= end_slot:
        all_slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=15)

    # 3) Ustalamy granice całego dnia (00:00:00–23:59:59)
    start_of_day = datetime.combine(date, time(hour=0, minute=0, second=0))
    end_of_day = datetime.combine(date, time(hour=23, minute=59, second=59))

    # 4) Pobieramy z bazy wszystkie wizyty lekarza w tym dniu
    appointments = (
        db
        .query(AppointmentModel)
        .filter(
            AppointmentModel.doctor_id == doctor_id,
            AppointmentModel.visit_datetime >= start_of_day,
            AppointmentModel.visit_datetime <= end_of_day
        )
        .all()
    )

    # 5) Wyciągamy zestaw zajętych kwadransów w formacie "HH:MM"
    busy_slots = {app.visit_datetime.strftime("%H:%M") for app in appointments}

    # 6) Tworzymy listę wolnych slotów
    free_slots = [slot for slot in all_slots if slot not in busy_slots]
    return free_slots
