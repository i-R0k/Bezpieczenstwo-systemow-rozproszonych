"""
Router do obsługi endpointów związanych z użytkownikami.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..app import schemas, crud
from ..app.database import SessionLocal

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register_client(user: schemas.ClientCreate, db: Session = Depends(get_db)):
    if user.role != "klient":
        raise HTTPException(status_code=400, detail="Self registration is allowed only for clients")
    db_user = crud.create_user(db, user)
    if db_user is None:
        raise HTTPException(status_code=400, detail="Użytkownik o podanym adresie e-mail już istnieje")
    return db_user

@router.post("/create-doctor", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def create_doctor(user: schemas.DoctorCreate, db: Session = Depends(get_db)):
    if user.role != "lekarz":
        raise HTTPException(status_code=400, detail="Role must be 'lekarz'")
    db_user = crud.create_user(db, user)
    if db_user is None:
        raise HTTPException(status_code=400, detail="User with that email already exists")
    return db_user

@router.post("/create-consultant", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def create_consultant(user: schemas.ConsultantCreate, db: Session = Depends(get_db)):
    if user.role != "konsultant":
        raise HTTPException(status_code=400, detail="Role must be 'konsultant'")
    db_user = crud.create_user(db, user)
    if db_user is None:
        raise HTTPException(status_code=400, detail="User with that email already exists")
    return db_user


@router.get("/", response_model=List[schemas.UserOut])
def read_users(db: Session = Depends(get_db)):
    users = crud.get_users(db)
    return users