from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Union, Optional
from vetclinic_api.validators import (
    validate_letters,
    validate_email,
    validate_phone_number,
    validate_permit_number,
    validate_postal_code,
)

# ---------------------------------------------------------------------
# Base schemas
# ---------------------------------------------------------------------
class UserBase(BaseModel):
    first_name: str
    last_name: str

    @field_validator("first_name", "last_name")
    def validate_names(cls, v):
        return validate_letters(v)


# ---------------------------------------------------------------------
# Create schemas
# ---------------------------------------------------------------------
class ClientCreate(UserBase):
    password: str
    role: str
    email: EmailStr
    phone_number: str
    address: str
    postal_code: str

    @field_validator("phone_number")
    def validate_phone(cls, v):
        return validate_phone_number(v)

    @field_validator("postal_code")
    def validate_postal(cls, v):
        return validate_postal_code(v)


class DoctorCreate(UserBase):
    specialization: str
    permit_number: str
    backup_email: EmailStr
    email: Optional[EmailStr] = None

    @field_validator("permit_number")
    def validate_permit(cls, v):
        return validate_permit_number(v)


class ConsultantCreate(UserBase):
    password: Optional[str] = None
    email: EmailStr
    role: str = "consultant"
    facility_id: int
    backup_email: EmailStr

    @field_validator("email")
    def validate_consultant_email(cls, v):
        return validate_email(v, role="consultant")


UserCreate = Union[ClientCreate, DoctorCreate, ConsultantCreate]


# ---------------------------------------------------------------------
# Update schema
# ---------------------------------------------------------------------
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    facility_id: Optional[int] = None
    backup_email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    specialization: Optional[str] = None
    permit_number: Optional[str] = None

    @field_validator("first_name", "last_name", mode="before")
    def validate_optional_names(cls, v):
        return validate_letters(v) if v is not None else v

    @field_validator("email")
    def validate_email_field(cls, v, info):
        return validate_email(v, role=info.data.get("role")) if v is not None else v

    @field_validator("phone_number")
    def validate_phone_optional(cls, v):
        return validate_phone_number(v) if v is not None else v

    @field_validator("postal_code")
    def validate_postal_optional(cls, v):
        return validate_postal_code(v) if v is not None else v

    @field_validator("permit_number")
    def validate_permit_optional(cls, v):
        return validate_permit_number(v) if v is not None else v


UserUpdateUnion = Union[ClientCreate, DoctorCreate, ConsultantCreate, UserUpdate]


# ---------------------------------------------------------------------
# Output schemas
# ---------------------------------------------------------------------
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
    def empty_backup_email_to_none(cls, v):
        return None if isinstance(v, str) and not v else v

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
    def empty_backup_email_to_none(cls, v):
        return None if isinstance(v, str) and not v else v

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None


class ConfirmTOTP(BaseModel):
    email: EmailStr
    totp_code: str
