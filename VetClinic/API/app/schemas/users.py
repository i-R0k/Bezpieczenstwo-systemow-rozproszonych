from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Union
from typing import Optional
from app.validators import (
    validate_letters,
    validate_email,
    validate_phone_number,
    validate_permit_number,
    validate_postal_code,
)

# Schemat bazowy dla użytkowników
class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr

    @field_validator("first_name")
    def validate_first_name(cls, value):
        return validate_letters(value)

    @field_validator("last_name")
    def validate_last_name(cls, value):
        return validate_letters(value)


# Schemat dla klienta
class ClientCreate(UserBase):
    password: str
    role: str  # powinno być "klient"
    phone_number: str
    address: str
    postal_code: str

    @field_validator("phone_number")
    def check_phone_number(cls, value):
        return validate_phone_number(value)
    
    @field_validator("postal_code")
    def check_postal_code(cls, value):
        return validate_postal_code(value)


# Schemat dla lekarza
class DoctorCreate(UserBase):
    password: str
    role: str  # powinno być "lekarz"
    specialization: str
    permit_number: str

    @field_validator("permit_number")
    def check_permit_number(cls, value):
        return validate_permit_number(value)
    
    @field_validator("email")
    def validate_doctor_email(cls, value, info):
        role = info.data.get("role")
        return validate_email(value, role=role)


# Schemat dla konsultanta
class ConsultantCreate(UserBase):
    password: str
    role: str  # powinno być "konsultant"

    @field_validator("email")
    def validate_consultant_email(cls, value, info):
        role = info.data.get("role")
        return validate_email(value, role=role)


# Alias unii dla tworzenia użytkownika – pozwala nam przyjmować jeden typ, który może być klientem, lekarzem lub konsultantem.
UserCreate = Union[ClientCreate, DoctorCreate, ConsultantCreate]


# Schemat wyjściowy (dla zwracania danych użytkownika z API)
class UserOut(UserBase):
    id: int
    role: str

    model_config = ConfigDict(from_attributes=True)


# Schemat do logowania użytkownika
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None

class ConfirmTOTP(BaseModel):
    email: EmailStr
    totp_code: str