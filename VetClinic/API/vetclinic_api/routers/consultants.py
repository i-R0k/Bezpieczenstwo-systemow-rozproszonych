from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from vetclinic_api.schemas.users import UserCreate, UserOut, UserUpdate
from vetclinic_api.crud.users_crud import get_users, get_user, create_user, update_user, delete_user
from vetclinic_api.core.database import get_db

router = APIRouter(prefix="/consultants", tags=["consultants"])

@router.get("/", response_model=List[UserOut])
def list_consultants(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    all_users = get_users(db)
    consultants = [u for u in all_users if u.role == "konsultant"]
    return consultants[skip : skip + limit]

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def add_consultant(user: UserCreate, db: Session = Depends(get_db)):
    user.role = "konsultant"
    return create_user(db, user)

@router.get("/{id}", response_model=UserOut)
def read_consultant(id: int, db: Session = Depends(get_db)):
    u = get_user(db, id)
    if not u or u.role != "konsultant":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Consultant not found")
    return u

@router.put("/{id}", response_model=UserOut)
def modify_consultant(id: int, user: UserUpdate, db: Session = Depends(get_db)):
    existing = get_user(db, id)
    if not existing or existing.role != "konsultant":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Consultant not found")
    return update_user(db, id, user)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_consultant(id: int, db: Session = Depends(get_db)):
    existing = get_user(db, id)
    if not existing or existing.role != "konsultant":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Consultant not found")
    delete_user(db, id)
