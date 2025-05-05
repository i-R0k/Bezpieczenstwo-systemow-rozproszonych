from vetclinic_gui.services.db import SessionLocal
from vetclinic_api.crud.appointments_crud import (
    get_appointments, get_appointment,
    create_appointment as crud_create_appointment,
    update_appointment as crud_update_appointment,
    delete_appointment as crud_delete_appointment
)
from vetclinic_api.schemas.appointment import AppointmentCreate, AppointmentUpdate

class AppointmentService:
    """
    Serwis CRUD dla zasobu wizyt, korzystający z funkcji w app.crud.appointment_crud.
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
