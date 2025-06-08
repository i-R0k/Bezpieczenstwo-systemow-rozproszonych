from vetclinic_gui.services.db import SessionLocal
from vetclinic_api.crud.medical_records import (
    list_medical_records,
    list_medical_records_by_appointment,
    get_medical_record,
    create_medical_record as crud_create_medical_record,
    update_medical_record as crud_update_medical_record,
    delete_medical_record as crud_delete_medical_record
)
from vetclinic_api.schemas.medical_records import MedicalRecordCreate, MedicalRecordUpdate

class MedicalRecordsService:
    """
    Serwis do zarządzania historią medyczną zwierząt.
    """
    @staticmethod
    def list(skip: int = 0, limit: int = 100):
        db = SessionLocal()
        try:
            return list_medical_records(db, skip=skip, limit=limit)
        finally:
            db.close()

    @staticmethod
    def list_by_appointment(appointment_id: int):
        db = SessionLocal()
        try:
            return list_medical_records_by_appointment(db, appointment_id)
        finally:
            db.close()

    def list_by_animal(animal_id: int):
        db = SessionLocal()
        try:
            all_recs = list_medical_records(db, skip=0, limit=1000)
            return [r for r in all_recs if getattr(r, "animal_id", None) == animal_id]
        finally:
            db.close()

    @staticmethod
    def get(record_id: int):
        db = SessionLocal()
        try:
            return get_medical_record(db, record_id)
        finally:
            db.close()

    @staticmethod
    def create(data: dict):
        db = SessionLocal()
        try:
            rec_in = MedicalRecordCreate(**data)
            return crud_create_medical_record(db, rec_in)
        finally:
            db.close()

    @staticmethod
    def update(record_id: int, data: dict):
        db = SessionLocal()
        try:
            rec_in = MedicalRecordUpdate(**data)
            return crud_update_medical_record(db, record_id, rec_in)
        finally:
            db.close()

    @staticmethod
    def delete(record_id: int):
        db = SessionLocal()
        try:
            return crud_delete_medical_record(db, record_id)
        finally:
            db.close()

# Alias for import compatibility
MedicalRecordService = MedicalRecordsService
