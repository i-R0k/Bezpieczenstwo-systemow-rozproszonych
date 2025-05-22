from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Union, Optional, Literal
from vetclinic_api.validators import (
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
    password: Optional[str] = None
    role: str = "consultant"
    facility_id: int 
    backup_email: EmailStr

    @field_validator("email")
    def validate_consultant_email(cls, value, info):
        if value is not None:
            return validate_email(value, role="consultant")
        return value


UserCreate = Union[ClientCreate, DoctorCreate, ConsultantCreate]

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    facility_id: Optional[int]      = None
    backup_email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    specialization: Optional[str] = None
    permit_number: Optional[str] = None

    @field_validator("first_name")
    def validate_first_name(cls, value):
        if value is not None:
            return validate_letters(value)
        return value

    @field_validator("last_name")
    def validate_last_name(cls, value):
        if value is not None:
            return validate_letters(value)
        return value

    @field_validator("email")
    def validate_email_field(cls, value, info):
        if value is not None:
            role = info.data.get("role")
            return validate_email(value, role=role)
        return value

    @field_validator("phone_number")
    def validate_phone(cls, value):
        if value is not None:
            return validate_phone_number(value)
        return value

    @field_validator("postal_code")
    def validate_postal(cls, value):
        if value is not None:
            return validate_postal_code(value)
        return value

    @field_validator("permit_number")
    def validate_permit(cls, value):
        if value is not None:
            return validate_permit_number(value)
        return value

# Alias unii dla aktualizacji użytkownika (dowolna z ról)
UserUpdateUnion = Union[ClientCreate, DoctorCreate, ConsultantCreate, UserUpdate]

# Schemat wyjściowy (dla zwracania danych użytkownika z API)
class ClientOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    address: str
    postal_code: str

    model_config = ConfigDict(from_attributes=True)


class DoctorOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    backup_email: Optional[EmailStr] = None
    specialization: str
    permit_number: str

    @field_validator("backup_email", mode="before")
    def _empty_str_to_none(cls, v):
        if isinstance(v, str) and not v:
            return None
        return v

    model_config = ConfigDict(from_attributes=True)


class ConsultantOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    facility_id: int
    backup_email: Optional[EmailStr] = None
    must_change_password: Optional[bool] = None

    @field_validator("backup_email", mode="before")
    def _empty_str_to_none(cls, v):
        if isinstance(v, str) and not v:
            return None
        return v

    model_config = ConfigDict(from_attributes=True)


# Schemat do logowania użytkownika
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None

class ConfirmTOTP(BaseModel):
    email: EmailStr
    totp_code: str