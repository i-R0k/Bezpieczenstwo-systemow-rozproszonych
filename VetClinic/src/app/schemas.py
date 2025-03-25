"""
Definicje schematów Pydantic służących do walidacji danych wejściowych oraz serializacji danych wyjściowych.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
import datetime

# Schemat dla użytkownika (używany np. przy rejestracji lub zwracaniu danych)
class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str  # Hasło przesyłane przy rejestracji

class UserOut(UserBase):
    id: int
    role: str

    class Config:
        orm_mode = True

# Możesz dodać inne schematy, np. dla Animal, Appointment itp.
