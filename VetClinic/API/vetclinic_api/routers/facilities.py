from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from vetclinic_api.schemas.facility import FacilityCreate, FacilityRead, FacilityUpdate
from vetclinic_api.crud.facility_crud import (
    get_facilities, get_facility, create_facility,
    update_facility, delete_facility
)
from vetclinic_api.core.database import get_db

router = APIRouter(prefix="/facilities", tags=["facilities"])

@router.get("/", response_model=List[FacilityRead])
def list_facilities(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_facilities(db, skip, limit)

@router.post("/", response_model=FacilityRead, status_code=status.HTTP_201_CREATED)
def add_facility(f: FacilityCreate, db: Session = Depends(get_db)):
    return create_facility(db, f)

@router.get("/{facility_id}", response_model=FacilityRead)
def read_facility(facility_id: int, db: Session = Depends(get_db)):
    db_f = get_facility(db, facility_id)
    if not db_f:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Facility not found")
    return db_f

@router.put("/{facility_id}", response_model=FacilityRead)
def modify_facility(facility_id: int, f: FacilityUpdate, db: Session = Depends(get_db)):
    db_f = update_facility(db, facility_id, f)
    if not db_f:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Facility not found")
    return db_f

@router.delete("/{facility_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_facility(facility_id: int, db: Session = Depends(get_db)):
    delete_facility(db, facility_id)
