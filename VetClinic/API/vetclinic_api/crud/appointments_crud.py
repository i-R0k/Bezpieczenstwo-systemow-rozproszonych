from typing import List

from sqlalchemy.orm import Session
from vetclinic_api.models.appointments import Appointment as AppointmentModel
from vetclinic_api.schemas.appointment import AppointmentCreate, AppointmentUpdate


def get_appointment(db: Session, appointment_id: int):
    return db.query(AppointmentModel).filter(AppointmentModel.id == appointment_id).first()


def get_appointments(db: Session, skip: int = 0, limit: int = 100) -> List[AppointmentModel]:
    return db.query(AppointmentModel).offset(skip).limit(limit).all()


def create_appointment(db: Session, appointment: AppointmentCreate) -> AppointmentModel:
    db_appointment = AppointmentModel(**appointment.model_dump())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


def update_appointment(db: Session, appointment_id: int, appointment: AppointmentUpdate) -> AppointmentModel | None:
    db_appointment = get_appointment(db, appointment_id)
    if not db_appointment:
        return None
    update_data = appointment.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_appointment, key, value)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


def get_appointments_by_owner(db: Session, owner_id: int) -> List[AppointmentModel]:
    """
    Zwraca wszystkie wizyty należące do zadanego klienta (owner_id).
    """
    return (
        db.query(AppointmentModel)
          .filter(AppointmentModel.owner_id == owner_id)
          .all()
    )


def delete_appointment(db: Session, appointment_id: int) -> AppointmentModel | None:
    db_appointment = get_appointment(db, appointment_id)
    if not db_appointment:
        return None
    db.delete(db_appointment)
    db.commit()
    return db_appointment
