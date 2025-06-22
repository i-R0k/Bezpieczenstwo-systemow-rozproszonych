from typing import List
from decimal import Decimal

from sqlalchemy.orm import Session

from vetclinic_api.models.appointments import Appointment as AppointmentModel
from vetclinic_api.schemas.appointment import AppointmentCreate, AppointmentUpdate

# import modułu do faktur
from vetclinic_api.crud.invoice_crud import create_invoice
from vetclinic_api.schemas.invoice import InvoiceCreate


def get_appointment(db: Session, appointment_id: int) -> AppointmentModel | None:
    """Zwraca wizytę o podanym ID lub None."""
    return db.query(AppointmentModel).filter(AppointmentModel.id == appointment_id).first()


def get_appointments(db: Session, skip: int = 0, limit: int = 100) -> List[AppointmentModel]:
    """Zwraca listę wizyt z paginacją."""
    return db.query(AppointmentModel).offset(skip).limit(limit).all()


def create_appointment(db: Session, appt_in: AppointmentCreate) -> AppointmentModel:
    """
    Tworzy wizytę oraz automatycznie generuje fakturę.
    Pobiera opłatę z pola `fee` w AppointmentCreate.
    """
    # 1. Utworzenie i zapis wizyty
    data = appt_in.model_dump()
    db_appointment = AppointmentModel(**data)
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)

    # 2. Pobranie opłaty z inputu
    amount = Decimal(str(appt_in.fee))

    # 3. Stworzenie faktury
    inv_in = InvoiceCreate(
        client_id=db_appointment.owner_id,
        amount=amount
    )
    create_invoice(db, inv_in)

    return db_appointment


def update_appointment(
    db: Session,
    appointment_id: int,
    appt_upd: AppointmentUpdate
) -> AppointmentModel | None:
    """Aktualizuje wizytę o podanym ID."""
    db_appointment = get_appointment(db, appointment_id)
    if not db_appointment:
        return None

    update_data = appt_upd.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(db_appointment, key, val)

    db.commit()
    db.refresh(db_appointment)
    return db_appointment


def get_appointments_by_owner(db: Session, owner_id: int) -> List[AppointmentModel]:
    """Zwraca wszystkie wizyty klienta o danym owner_id."""
    return (
        db.query(AppointmentModel)
          .filter(AppointmentModel.owner_id == owner_id)
          .all()
    )


def delete_appointment(db: Session, appointment_id: int) -> AppointmentModel | None:
    """Usuwa wizytę o danym ID."""
    db_appointment = get_appointment(db, appointment_id)
    if not db_appointment:
        return None
    db.delete(db_appointment)
    db.commit()
    return db_appointment
