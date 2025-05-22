from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from vetclinic_api.core.database import get_db
from vetclinic_api.crud.consultants import (
    create_consultant, list_consultants,
    get_consultant, update_consultant, delete_consultant
)
from vetclinic_api.schemas.users import ConsultantCreate, ConsultantOut, UserUpdate

router = APIRouter(prefix="/consultants", tags=["consultants"])

@router.get("/", response_model=List[ConsultantOut])
def read_consultants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return list_consultants(db, skip=skip, limit=limit)


@router.post("/", response_model=ConsultantOut, status_code=status.HTTP_201_CREATED)
def create_consultant_endpoint(user: ConsultantCreate, db: Session = Depends(get_db)):
    return create_consultant(db, user)


@router.get("/{consultant_id}", response_model=ConsultantOut)
def read_consultant(consultant_id: int, db: Session = Depends(get_db)):
    c = get_consultant(db, consultant_id)
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Consultant not found")
    return c

@router.put("/{consultant_id}", response_model=ConsultantOut)
def update_consultant_endpoint(consultant_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    c = update_consultant(db, consultant_id, data)
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Consultant not found")
    return c


@router.delete("/{consultant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_consultant_endpoint(consultant_id: int, db: Session = Depends(get_db)):
    ok = delete_consultant(db, consultant_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Consultant not found")
