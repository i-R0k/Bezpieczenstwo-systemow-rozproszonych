from vetclinic_api.crud.facility_crud import (
    get_facilities, get_facility,
    create_facility, update_facility, delete_facility
)
from vetclinic_api.core.database import SessionLocal
from vetclinic_api.schemas.facility import FacilityCreate, FacilityUpdate, FacilityRead

class FacilityService:
    @staticmethod
    def list():
        db = SessionLocal()
        try:
            facilities = get_facilities(db)
            # Możesz owinąć w FacilityRead, jeśli chcesz zawsze wyjściowy model
            return [FacilityRead.model_validate(fac) for fac in facilities]
        finally:
            db.close()

    @staticmethod
    def get(fid: int):
        db = SessionLocal()
        try:
            fac = get_facility(db, fid)
            return FacilityRead.model_validate(fac) if fac else None
        finally:
            db.close()

    @staticmethod
    def create(data: dict):
        db = SessionLocal()
        try:
            facility_in = FacilityCreate(**data)
            fac = create_facility(db, facility_in)
            return FacilityRead.model_validate(fac)
        finally:
            db.close()

    @staticmethod
    def update(fid: int, data: dict):
        db = SessionLocal()
        try:
            facility_in = FacilityUpdate(**data)
            fac = update_facility(db, fid, facility_in)
            return FacilityRead.model_validate(fac) if fac else None
        finally:
            db.close()

    @staticmethod
    def delete(fid: int):
        db = SessionLocal()
        try:
            return delete_facility(db, fid)
        finally:
            db.close()
