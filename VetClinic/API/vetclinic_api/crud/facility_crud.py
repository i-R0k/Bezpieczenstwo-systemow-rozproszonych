from sqlalchemy.orm import Session
from vetclinic_api.models.facility import Facility
from vetclinic_api.schemas.facility import FacilityCreate, FacilityUpdate

def get_facilities(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Facility).offset(skip).limit(limit).all()

def get_facility(db: Session, facility_id: int):
    return db.query(Facility).filter(Facility.id == facility_id).first()

def create_facility(db: Session, f: FacilityCreate):
    db_f = Facility(**f.dict())
    db.add(db_f)
    db.commit()
    db.refresh(db_f)
    return db_f

def update_facility(db: Session, facility_id: int, f: FacilityUpdate):
    db_f = get_facility(db, facility_id)
    if not db_f:
        return None
    for key, val in f.dict(exclude_unset=True).items():
        setattr(db_f, key, val)
    db.commit()
    db.refresh(db_f)
    return db_f

def delete_facility(db: Session, facility_id: int):
    db_f = get_facility(db, facility_id)
    if db_f:
        db.delete(db_f)
        db.commit()
