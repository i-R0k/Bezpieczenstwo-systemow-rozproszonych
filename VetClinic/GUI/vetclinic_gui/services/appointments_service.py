from vetclinic_gui.services.db import SessionLocal
from vetclinic_api.crud.appointments_crud import (
    get_appointments as crud_get_appointments,
    get_appointments_by_owner as crud_get_appointments_by_owner,
    get_appointment as crud_get_appointment,
    create_appointment as crud_create_appointment,
    update_appointment as crud_update_appointment,
    delete_appointment as crud_delete_appointment,
)
from vetclinic_api.schemas.appointment import AppointmentCreate, AppointmentUpdate
from vetclinic_api.models.appointments import Appointment as AppointmentModel
from sqlalchemy.orm import Session, selectinload
from datetime import datetime, date, time, timedelta
from typing import List


class AppointmentService:
    @staticmethod
    def list() -> List[AppointmentModel]:
        """
        Zwraca wszystkie wizyty wraz z załadowanym doktorem.
        """
        db: Session = SessionLocal()
        try:
            return (
                db.query(AppointmentModel)
                  .options(selectinload(AppointmentModel.doctor))
                  .all()
            )
        finally:
            db.close()

    @staticmethod
    def get(appointment_id: int) -> AppointmentModel:
        """
        Zwraca wizytę o danym ID wraz z obiektem doctor.
        """
        db: Session = SessionLocal()
        try:
            return (
                db.query(AppointmentModel)
                  .options(selectinload(AppointmentModel.doctor))
                  .filter(AppointmentModel.id == appointment_id)
                  .one_or_none()
            )
        finally:
            db.close()

    @staticmethod
    def create(data: dict) -> AppointmentModel:
        """
        Tworzy nową wizytę na podstawie danych i zwraca ją.
        """
        db: Session = SessionLocal()
        try:
            appt_in = AppointmentCreate(**data)
            appt = crud_create_appointment(db, appt_in)
            return appt
        finally:
            db.close()

    @staticmethod
    def update(appointment_id: int, data: dict) -> AppointmentModel:
        """
        Aktualizuje wizytę o podanym ID i zwraca ją.
        """
        db: Session = SessionLocal()
        try:
            appt_in = AppointmentUpdate(**data)
            return crud_update_appointment(db, appointment_id, appt_in)
        finally:
            db.close()

    @staticmethod
    def delete(appointment_id: int) -> None:
        """
        Usuwa wizytę o podanym ID.
        """
        db: Session = SessionLocal()
        try:
            crud_delete_appointment(db, appointment_id)
        finally:
            db.close()

    @staticmethod
    def list_by_owner(owner_id: int) -> List[AppointmentModel]:
        """
        Zwraca wszystkie wizyty klienta wraz z załadowanym obiektem doctor.
        """
        db: Session = SessionLocal()
        try:
            return (
                db.query(AppointmentModel)
                  .options(selectinload(AppointmentModel.doctor))
                  .filter(AppointmentModel.owner_id == owner_id)
                  .all()
            )
        finally:
            db.close()

    @staticmethod
    def get_free_slots(doctor_id: int, date_str: str) -> List[str]:
        """
        Zwraca wolne sloty co 15 minut (08:00–18:45) dla lekarza w danym dniu.
        """
        # Parsowanie daty
        try:
            target_date: date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return []

        # Niedziela – brak pracy
        if target_date.weekday() == 6:
            return []

        db: Session = SessionLocal()
        try:
            start_of_day = datetime.combine(target_date, time(0, 0))
            end_of_day = datetime.combine(target_date, time(23, 59, 59))

            apps = (
                db.query(AppointmentModel)
                  .filter(
                      AppointmentModel.doctor_id == doctor_id,
                      AppointmentModel.visit_datetime >= start_of_day,
                      AppointmentModel.visit_datetime <= end_of_day,
                  )
                  .all()
            )

            busy_slots = {app.visit_datetime.strftime("%H:%M") for app in apps}

            free_slots: List[str] = []
            current_dt = datetime.combine(target_date, time(8, 0))
            end_slot = datetime.combine(target_date, time(18, 45))
            while current_dt <= end_slot:
                slot = current_dt.strftime("%H:%M")
                if slot not in busy_slots:
                    free_slots.append(slot)
                current_dt += timedelta(minutes=15)

            return free_slots
        finally:
            db.close()
