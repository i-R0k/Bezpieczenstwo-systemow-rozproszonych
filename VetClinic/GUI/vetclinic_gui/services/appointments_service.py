from vetclinic_gui.services.db import SessionLocal
from vetclinic_api.crud.appointments_crud import (
    get_appointments, get_appointment,
    create_appointment as crud_create_appointment,
    update_appointment as crud_update_appointment,
    delete_appointment as crud_delete_appointment,
    get_appointments_by_owner as get_appointments_by_owner
)
from vetclinic_api.schemas.appointment import AppointmentCreate, AppointmentUpdate
from vetclinic_api.models.appointments import Appointment as AppointmentModel
from sqlalchemy.orm import Session
from datetime import datetime, date, time, timedelta
from typing import List

class AppointmentService:
    """
    Serwis CRUD dla zasobu wizyt, korzystający z funkcji w app.crud.appointment_crud.
    Dodatkowo metoda get_free_slots, która zwraca wolne sloty co 15 minut
    w godzinach 08:00–18:45 dla danego lekarza i daty (pon–sob).
    """
    @staticmethod
    def list():
        db = SessionLocal()
        try:
            return get_appointments(db)
        finally:
            db.close()

    @staticmethod
    def get(appointment_id: int):
        db = SessionLocal()
        try:
            return get_appointment(db, appointment_id)
        finally:
            db.close()

    @staticmethod
    def create(data: dict):
        db = SessionLocal()
        try:
            appt_in = AppointmentCreate(**data)
            return crud_create_appointment(db, appt_in)
        finally:
            db.close()

    @staticmethod
    def update(appointment_id: int, data: dict):
        db = SessionLocal()
        try:
            appt_in = AppointmentUpdate(**data)
            return crud_update_appointment(db, appointment_id, appt_in)
        finally:
            db.close()

    @staticmethod
    def delete(appointment_id: int):
        db = SessionLocal()
        try:
            return crud_delete_appointment(db, appointment_id)
        finally:
            db.close()
    
    @staticmethod
    def list_by_owner(owner_id: int):
        """
        Zwraca listę wszystkich wizyt (Appointment) dla danego klienta (owner_id).
        """
        db = SessionLocal()
        try:
            return get_appointments_by_owner(db, owner_id)
        finally:
            db.close()

    @staticmethod
    def get_free_slots(doctor_id: int, date_str: str) -> List[str]:
        """
        Zwraca listę wolnych kwadransowych slotów ("HH:MM") od 08:00 do 18:45
        dla lekarza o podanym doctor_id w dniu date_str ("YYYY-MM-DD").
        Jeśli date_str to niedziela, zwraca pustą listę.
        """
        # Parsujemy date_str na date
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return []

        # Jeśli to niedziela (weekday == 6), lekarz nie przyjmuje
        if target_date.weekday() == 6:
            return []

        db: Session = SessionLocal()
        try:
            # Ustalamy początek i koniec dnia
            start_of_day = datetime.combine(target_date, time(hour=0, minute=0, second=0))
            end_of_day = datetime.combine(target_date, time(hour=23, minute=59, second=59))

            # Pobieramy wszystkie wizyty tego lekarza w wybranym dniu
            apps = (
                db.query(AppointmentModel)
                  .filter(
                      AppointmentModel.doctor_id == doctor_id,
                      AppointmentModel.visit_datetime >= start_of_day,
                      AppointmentModel.visit_datetime <= end_of_day
                  )
                  .all()
            )

            # Wyciągamy zestaw zajętych kwadransów "HH:MM"
            busy_slots = { app.visit_datetime.strftime("%H:%M") for app in apps }

            # Generujemy wszystkie możliwe kwadransy od 08:00 do 18:45
            all_slots = []
            current = datetime.combine(target_date, time(hour=8, minute=0))
            end_slot = datetime.combine(target_date, time(hour=18, minute=45))
            while current <= end_slot:
                all_slots.append(current.strftime("%H:%M"))
                current += timedelta(minutes=15)

            # Filtrujemy sloty, które nie są w busy_slots
            free_slots = [slot for slot in all_slots if slot not in busy_slots]
            return free_slots
        finally:
            db.close()
            
