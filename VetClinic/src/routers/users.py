"""
Router do obsługi endpointów związanych z użytkownikami.
"""

import datetime
import pyotp
from qrcode import make as generate_qr_code
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from ..app import schemas, crud
from ..app.database import SessionLocal
from ..app.auth import get_user_by_email, verify_password, create_access_token

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

@router.post("/login")
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Endpoint logowania:
    - Użytkownik wysyła email i hasło (oraz opcjonalnie totp_code).
    - Jeśli hasło jest poprawne, ale TOTP nie jest skonfigurowany (totp_secret jest pusty),
      generujemy nowy secret i provisioning URI, zwracając status 201 i informację o potrzebie konfiguracji.
    - Jeśli TOTP jest skonfigurowany, oczekujemy podania totp_code, który weryfikujemy.
    - Przy poprawnych danych generujemy token JWT.
    """
    user = get_user_by_email(db, user_credentials.email)
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email or password")
    
    # Jeżeli TOTP nie jest skonfigurowany, generujemy secret i provisioning URI
    if not user.totp_secret:
        totp_secret = pyotp.random_base32()
        totp = pyotp.TOTP(totp_secret)
        totp_uri = totp.provisioning_uri(name=user.email, issuer_name="VetClinic")
        # Zapisujemy nowo wygenerowany secret w bazie
        user.totp_secret = totp_secret
        db.commit()
        return JSONResponse(
            status_code=201,
            content={"need_totp": True, "totp_uri": totp_uri}
        )
    
    # Jeśli TOTP jest skonfigurowany, oczekujemy, że użytkownik poda kod TOTP
    if not user_credentials.totp_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP code required")
    
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(user_credentials.totp_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code")
    
    # Wszystko w porządku – generujemy token JWT
    token_payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
    }
    access_token = create_access_token(data=token_payload, expires_delta=datetime.timedelta(hours=1))
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/setup-totp")
def setup_totp(email: str, db: Session = Depends(get_db)):
    # Znajdź użytkownika po emailu (przeszukaj wszystkie tabele, np. przez funkcję get_user_by_email)
    user = crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Wygeneruj secret TOTP
    totp_secret = pyotp.random_base32()
    # Generuj URI do konfiguracji
    totp_uri = pyotp.TOTP(totp_secret).provisioning_uri(name=email, issuer_name="VetClinic")
    # Zapisz secret do użytkownika – zakładamy, że model posiada pole totp_secret
    user.totp_secret = totp_secret
    db.commit()
    
    # Opcjonalnie: zapisz QR kod do pliku, lub zwróć URI do wyświetlenia w GUI
    qr_filename = f"{email}_qrcode.png"
    generate_qr_code(totp_uri, filename=qr_filename)
    
    return {"message": "TOTP configured", "totp_uri": totp_uri, "qr_code": qr_filename}


@router.post("/confirm-totp")
def confirm_totp(payload: schemas.ConfirmTOTP, db: Session = Depends(get_db)):
    """
    Potwierdza TOTP na podstawie emaila i kodu TOTP.
    """
    user = get_user_by_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.totp_secret:
        raise HTTPException(status_code=400, detail="TOTP secret is not configured")
    
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(payload.totp_code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")
    
    # Zwracamy np. status 200
    return {"detail": "TOTP confirmed"}
