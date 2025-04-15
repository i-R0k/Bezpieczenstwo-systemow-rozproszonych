"""
Router do obsługi endpointów związanych z użytkownikami.
"""

import datetime
import pyotp
from qrcode import make as generate_qr_code
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from app.crud import users_crud as crud
from app.schemas import users as schemas
from app.core.database import SessionLocal
from app.core.security import get_user_by_email, verify_password, create_access_token

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
def login(
    user_credentials: schemas.UserLogin,
    force_provision: bool = Query(False, description="Jeśli True, wymusza ponowną konfigurację TOTP"),
    db: Session = Depends(get_db)
):
    """
    Endpoint logowania:
      - Użytkownik przesyła email i hasło (oraz opcjonalnie totp_code).
      - Jeśli użytkownik nie ma ustawionego totp_secret lub (jeśli force_provision==True),
        generujemy nowy totp_secret i ustawiamy totp_confirmed na False,
        a następnie – jeżeli totp_code nie został podany – zwracamy provisioning URI (status 201).
      - Jeśli totp_code nie został podany, a TOTP jest już potwierdzony, zgłaszamy błąd.
      - Jeśli totp_code został podany, weryfikujemy go – przy poprawnych danych generujemy token JWT.
    """
    # Weryfikacja istnienia użytkownika oraz hasła
    user = get_user_by_email(db, user_credentials.email)
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password"
        )

    # Jeśli parametr force_provision jest ustawiony (True) lub użytkownik nie ma ustawionego totp_secret,
    # generujemy nowy totp_secret oraz ustawiamy totp_confirmed na False.
    if force_provision or not user.totp_secret:
        totp_secret = pyotp.random_base32()
        user.totp_secret = totp_secret
        user.totp_confirmed = False
        db.commit()

    # Jeśli w żądaniu nie podano totp_code
    if not user_credentials.totp_code:
        # Jeżeli TOTP nie został potwierdzony, zwracamy provisioning URI.
        if not user.totp_confirmed:
            totp = pyotp.TOTP(user.totp_secret)
            totp_uri = totp.provisioning_uri(name=user.email, issuer_name="VetClinic")
            return JSONResponse(
                status_code=201,
                content={"need_totp": True, "totp_uri": totp_uri}
            )
        else:
            # Jeśli TOTP jest potwierdzony, login bez totp_code jest niedozwolony.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TOTP code required"
            )

    # Jeśli totp_code został podany – weryfikujemy go.
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(user_credentials.totp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code"
        )

    # Przy poprawnej weryfikacji generujemy token JWT.
    token_payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
    }
    access_token = create_access_token(
        data=token_payload,
        expires_delta=datetime.timedelta(hours=1)
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}


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
def confirm_totp(confirm_data: schemas.ConfirmTOTP, db: Session = Depends(get_db)):
    """
    Endpoint potwierdzający konfigurację TOTP.
    
    Przyjmuje:
      - email: identyfikator użytkownika,
      - totp_code: 6-cyfrowy kod generowany przez aplikację TOTP.
    
    Jeśli użytkownik został znaleziony i posiada skonfigurowany totp_secret,
    a przesłany kod jest poprawny, ustawiamy flagę totp_confirmed na True i zwracamy komunikat w polu detail.
    """
    user = get_user_by_email(db, confirm_data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")
    
    if not user.totp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="TOTP is not configured for this user")
    
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(confirm_data.totp_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid TOTP code")
    
    user.totp_confirmed = True
    db.commit()
    return {"detail": "TOTP confirmed"}