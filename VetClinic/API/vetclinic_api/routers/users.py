import datetime
import pyotp
from datetime import timedelta
from typing import List
from qrcode import make as generate_qr_code

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from vetclinic_api.crud.users_crud import (
    create_client, list_clients, get_client,
    update_client, delete_client
)
from vetclinic_api.schemas.users import (
    ClientCreate, ClientOut, UserUpdate,
    UserLogin, ConfirmTOTP
)
from vetclinic_api.core.database import get_db
from vetclinic_api.core.security import (
    get_user_by_email, verify_password, create_access_token
)

router = APIRouter(prefix="/users", tags=["users"])

MAX_FAILS = 5
BLOCK_PERIOD = timedelta(minutes=15)


@router.post("/register", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def register_client(user: ClientCreate, db: Session = Depends(get_db)):
    if user.role != "klient":
        raise HTTPException(400, "Self-registration allowed only for clients")
    db_user = create_client(db, user)
    return db_user


@router.get("/", response_model=list[ClientOut])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = list_clients(db)
    return users[skip : skip + limit]


@router.get("/{user_id}", response_model=ClientOut)
def read_user(user_id: int, db: Session = Depends(get_db)):
    c = get_client(db, user_id)
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client not found")
    return c


@router.put("/{user_id}", response_model=ClientOut)
def update_user_endpoint(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    c = update_client(db, user_id, data)
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client not found")
    return c


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_endpoint(user_id: int, db: Session = Depends(get_db)):
    ok = delete_client(db, user_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client not found")

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_many_users(user_ids: List[int] = Body(...), db: Session = Depends(get_db)):
    for user_id in user_ids:
        delete_client(db, user_id)
    return

@router.post("/login")
def login(
    creds: UserLogin,
    force_provision: bool = Query(False, description="Force TOTP reprovision"),
    db: Session = Depends(get_db)
):
    now = datetime.datetime.utcnow()
    user = get_user_by_email(db, creds.email)

    # 1) Blokada
    if user and user.locked_until and user.locked_until > now:
        mins = int((user.locked_until - now).total_seconds() // 60) + 1
        raise HTTPException(status.HTTP_423_LOCKED,
            f"Konto zablokowane – spróbuj za {mins} min."
        )

    # 2) Email / hasło
    if not user or not verify_password(creds.password, user.password_hash):
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_FAILS:
                user.locked_until = now + BLOCK_PERIOD
                user.failed_login_attempts = 0
            db.commit()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nieprawidłowy email lub hasło")

    # 3) Reset liczników
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    # 4) Provisioning TOTP?
    if force_provision or not user.totp_secret:
        user.totp_secret = pyotp.random_base32()
        user.totp_confirmed = False
        db.commit()

    # jeżeli nie potwierdzono albo nie podano kodu – zwracamy URI
    if not creds.totp_code or not user.totp_confirmed:
        if not user.totp_confirmed:
            uri = pyotp.TOTP(user.totp_secret).provisioning_uri(
                name=user.email, issuer_name="VetClinic"
            )
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={"need_totp": True, "totp_uri": uri}
            )
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kod TOTP wymagany")

    # 5) weryfikacja kodu
    if not pyotp.TOTP(user.totp_secret).verify(creds.totp_code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nieprawidłowy kod TOTP")

    # 6) JWT
    token = create_access_token(
        data={"user_id": user.id, "email": user.email, "role": user.role},
        expires_delta=timedelta(hours=1)
    )
    return {"access_token": token, "token_type": "bearer", "role": user.role}


@router.post("/setup-totp")
def setup_totp(email: str, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(404, "User not found")
    user.totp_secret = pyotp.random_base32()
    user.totp_confirmed = False
    db.commit()
    uri = pyotp.TOTP(user.totp_secret).provisioning_uri(
        name=user.email, issuer_name="VetClinic"
    )
    qr_fn = f"{email}_qrcode.png"
    generate_qr_code(uri).save(qr_fn)
    return {"totp_uri": uri, "qr_code": qr_fn}


@router.post("/confirm-totp")
def confirm_totp(data: ConfirmTOTP, db: Session = Depends(get_db)):
    user = get_user_by_email(db, data.email)
    if not user or not user.totp_secret:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found or TOTP not set")
    if not pyotp.TOTP(user.totp_secret).verify(data.totp_code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid TOTP code")
    user.totp_confirmed = True
    db.commit()
    return {"detail": "TOTP confirmed"}
