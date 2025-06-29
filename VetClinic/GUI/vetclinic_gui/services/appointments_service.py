# vetclinic_gui/services/appointments_service.py

from datetime import datetime, date, time, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session, selectinload

from vetclinic_gui.services.db import SessionLocal
from vetclinic_api.models.appointments import Appointment as AppointmentModel


class AppointmentService:
    @staticmethod
    def list() -> List[AppointmentModel]:
        """
        Zwraca wszystkie wizyty wraz z załadowanym doktorem i właścicielem.
        """
        db: Session = SessionLocal()
        try:
            return (
                db.query(AppointmentModel)
                  .options(
                      selectinload(AppointmentModel.doctor),
                      selectinload(AppointmentModel.owner),
                  )
                  .all()
            )
        finally:
            db.close()

    @staticmethod
    def get(appointment_id: int) -> Optional[AppointmentModel]:
        """
        Zwraca wizytę o danym ID wraz z obiektami doctor i owner (eager‐load).
        """
        db: Session = SessionLocal()
        try:
            return (
                db.query(AppointmentModel)
                  .options(
                      selectinload(AppointmentModel.doctor),
                      selectinload(AppointmentModel.owner),
                  )
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
        # tutaj możesz nadal używać crud_create_appointment, 
        # ale zadbaj, by w crudach owner/doctora nie używać lazy‐load
        from vetclinic_api.crud.appointments_crud import create_appointment as crud_create

        db: Session = SessionLocal()
        try:
            appt = crud_create(db, data)
            return appt
        finally:
            db.close()

    @staticmethod
    def update(appointment_id: int, data: dict) -> AppointmentModel:
        """
        Aktualizuje wizytę o podanym ID i zwraca ją.
        """
        from vetclinic_api.crud.appointments_crud import update_appointment as crud_update

        db: Session = SessionLocal()
        try:
            appt = crud_update(db, appointment_id, data)
            return appt
        finally:
            db.close()

    @staticmethod
    def delete(appointment_id: int) -> None:
        """
        Usuwa wizytę o podanym ID.
        """
        from vetclinic_api.crud.appointments_crud import delete_appointment as crud_delete

        db: Session = SessionLocal()
        try:
            crud_delete(db, appointment_id)
        finally:
            db.close()

    @staticmethod
    def list_by_owner(owner_id: int) -> List[AppointmentModel]:
        """
        Zwraca wszystkie wizyty klienta wraz z obiektami doctor i owner.
        """
        db: Session = SessionLocal()
        try:
            return (
                db.query(AppointmentModel)
                  .options(
                      selectinload(AppointmentModel.doctor),
                      selectinload(AppointmentModel.owner),
                  )
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
            end_of_day   = datetime.combine(target_date, time(23, 59, 59))

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
            end_slot   = datetime.combine(target_date, time(18, 45))
            while current_dt <= end_slot:
                slot = current_dt.strftime("%H:%M")
                if slot not in busy_slots:
                    free_slots.append(slot)
                current_dt += timedelta(minutes=15)

            return free_slots
        finally:
            db.close()
