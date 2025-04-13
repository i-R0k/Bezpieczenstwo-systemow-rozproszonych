from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class AppointmentBase(BaseModel):
    visit_datetime: datetime = Field(..., description="Data i czas wizyty")
    reason: Optional[str] = Field(None, description="Powód wizyty lub rodzaj usługi")
    status: str = Field("zaplanowana", description="Status wizyty, np. zaplanowana, odwołana, zakończona")
    doctor_id: int = Field(..., description="ID lekarza obsługującego wizytę")
    animal_id: int = Field(..., description="ID zwierzęcia będącego pacjentem")
    owner_id: int = Field(..., description="ID właściciela zwierzęcia")
    notes: Optional[str] = Field(None, description="Dodatkowe uwagi")

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    visit_datetime: Optional[datetime] = Field(None, description="Data i czas wizyty")
    reason: Optional[str] = Field(None, description="Powód wizyty")
    status: Optional[str] = Field(None, description="Status wizyty")
    doctor_id: Optional[int] = Field(None, description="ID lekarza")
    animal_id: Optional[int] = Field(None, description="ID zwierzęcia")
    owner_id: Optional[int] = Field(None, description="ID właściciela")
    notes: Optional[str] = Field(None, description="Uwagi")

class Appointment(AppointmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        model_config = ConfigDict(from_attributes=True)
