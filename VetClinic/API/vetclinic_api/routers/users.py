"""
Router do obsługi endpointów związanych z użytkownikami.
"""

import datetime
import pyotp
from qrcode import make as generate_qr_code
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from vetclinic_api. crud import users_crud as crud
from vetclinic_api. schemas import users as schemas
from vetclinic_api. core.database import SessionLocal
from vetclinic_api. core.security import get_user_by_email, verify_password, create_access_token

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

MAX_FAILS = 5
BLOCK_SECONDS = 15 * 60

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
async def login(
    request: Request,
    user_credentials: schemas.UserLogin,
    force_provision: bool = Query(False, description="Jeśli True, wymusza ponowną konfigurację TOTP"),
    db: Session = Depends(get_db)
):
    """
    Endpoint logowania z blokadą po 5 nieudanych próbach (15 min).
    """
    redis = request.app.state.redis
    base_key = f"login:{user_credentials.email}"
    fails_key = f"{base_key}:fails"
    lock_key  = f"{base_key}:locked"

    # 1) Sprawdź, czy konto jest już zablokowane
    if await redis.exists(lock_key):
        ttl = await redis.ttl(lock_key)
        minutes = ttl // 60
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Konto zablokowane – spróbuj ponownie za {minutes} min."
        )

    # 2) Weryfikacja użytkownika i hasła
    user = get_user_by_email(db, user_credentials.email)
    if not user or not verify_password(user_credentials.password, user.password_hash):
        fails = await redis.incr(fails_key)
        if fails == 1:
            await redis.expire(fails_key, BLOCK_SECONDS)
        if fails >= MAX_FAILS:
            await redis.set(lock_key, "1", expire=BLOCK_SECONDS)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Zbyt wiele nieudanych prób – konto zablokowane na 15 min."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password"
        )

    # 3) Udane logowanie – reset licznika
    await redis.delete(fails_key)

    # 4) TOTP: wymuś provisioning jeśli trzeba
    if force_provision or not user.totp_secret:
        totp_secret = pyotp.random_base32()
        user.totp_secret = totp_secret
        user.totp_confirmed = False
        db.commit()

    if not user_credentials.totp_code:
        if not user.totp_confirmed:
            totp = pyotp.TOTP(user.totp_secret)
            totp_uri = totp.provisioning_uri(name=user.email, issuer_name="VetClinic")
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={"need_totp": True, "totp_uri": totp_uri}
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOTP code required"
        )

    # 5) Weryfikacja TOTP
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(user_credentials.totp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code"
        )

    # 6) Generowanie i zwrot tokena JWT
    payload = {"user_id": user.id, "email": user.email, "role": user.role}
    access_token = create_access_token(data=payload, expires_delta=datetime.timedelta(hours=1))
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