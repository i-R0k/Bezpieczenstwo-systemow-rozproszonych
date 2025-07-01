from typing import List, Optional
from decimal import Decimal

from sqlalchemy.orm import Session
from web3 import Web3

from vetclinic_api.models.appointments import Appointment as AppointmentModel
from vetclinic_api.schemas.appointment import AppointmentCreate, AppointmentUpdate

# CRUD do faktur
from vetclinic_api.crud.invoice_crud import create_invoice
from vetclinic_api.schemas.invoice import InvoiceCreate

# CRUD do blockchaina
from vetclinic_api.crud.blockchain_crud import add_record as blockchain_add_record


def get_appointment(db: Session, appointment_id: int) -> Optional[AppointmentModel]:
    """Zwraca wizytę o podanym ID lub None."""
    return db.query(AppointmentModel).filter(AppointmentModel.id == appointment_id).first()


def get_appointments(db: Session, skip: int = 0, limit: int = 100) -> List[AppointmentModel]:
    """Zwraca listę wizyt z paginacją."""
    return db.query(AppointmentModel).offset(skip).limit(limit).all()


def create_appointment(db: Session, appt_in: AppointmentCreate) -> AppointmentModel:
    """
    Tworzy wizytę, generuje fakturę i zapisuje rekord on‐chain.
    Zwraca encję Appointment z wypełnionym tx_hash.
    """
    # 1. Utworzenie i zapis wizyty w bazie
    data = appt_in.model_dump()
    db_appointment = AppointmentModel(**data)
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)

    # 2. Generujemy fakturę
    amount = Decimal(str(appt_in.fee))
    inv_in = InvoiceCreate(
        client_id=db_appointment.owner_id,
        amount=amount
    )
    create_invoice(db, inv_in)

    # 3. Przygotowanie danych do blockchaina i wysłanie transakcji
    try:
        # hashujemy np. "id-timestamp"
        payload = f"{db_appointment.id}-{db_appointment.visit_datetime.isoformat()}"
        data_hash = Web3.to_hex(Web3.keccak(text=payload))
        tx_hash = blockchain_add_record(db_appointment.id, data_hash)
        # zapisujemy tx_hash w kolumnie Appointment.tx_hash (dodaj ją w modelu!)
        db_appointment.tx_hash = tx_hash
        db.commit()
        db.refresh(db_appointment)
    except Exception as e:
        # jeśli blockchain nie odpowiada, logujemy i zwracamy encję bez tx_hash
        # (możesz zmienić na raise, jeśli chcesz przerywać w takim wypadku)
        print(f"⚠️  Ostrzeżenie: nie udało się zapisać wizyty on‐chain: {e}")

    return db_appointment


def update_appointment(
    db: Session,
    appointment_id: int,
    appt_upd: AppointmentUpdate
) -> Optional[AppointmentModel]:
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


def delete_appointment(db: Session, appointment_id: int) -> Optional[AppointmentModel]:
    """Usuwa wizytę o danym ID."""
    db_appointment = get_appointment(db, appointment_id)
    if not db_appointment:
        return None
    db.delete(db_appointment)
    db.commit()
    return db_appointment
