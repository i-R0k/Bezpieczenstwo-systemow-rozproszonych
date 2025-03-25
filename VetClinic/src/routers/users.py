"""
Router do obsługi endpointów związanych z użytkownikami.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..app import schemas, crud
from ..app.database import SessionLocal

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

# Dependency – funkcja otwierająca sesję do bazy danych
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Sprawdzenie, czy użytkownik już istnieje (przykładowo, możesz to rozszerzyć)
    db_user = db.query(crud).filter(crud.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user)
