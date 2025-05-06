from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class AppointmentBase(BaseModel):
    visit_datetime: datetime = Field(
        ..., description="Data i czas wizyty"
    )
    reason: Optional[str] = Field(
        None, description="Powód wizyty lub rodzaj usługi"
    )
    treatment: Optional[str] = Field(
        None, description="Zastosowane leczenie podczas wizyty"
    )
    priority: str = Field(
        "normalna",
        description="Priorytet wizyty: normalna, pilna, nagła"
    )
    weight: Optional[float] = Field(
        None, description="Waga zwierzęcia w dniu wizyty (kg)"
    )

    doctor_id: int = Field(
        ..., description="ID lekarza obsługującego wizytę"
    )
    animal_id: int = Field(
        ..., description="ID zwierzęcia będącego pacjentem"
    )
    owner_id: int = Field(
        ..., description="ID właściciela zwierzęcia"
    )
    notes: Optional[str] = Field(
        None, description="Dodatkowe uwagi"
    )

    # dzięki temu możemy zwracać ORM-owe modele w odpowiedziach
    model_config = ConfigDict(from_attributes=True)


class AppointmentCreate(AppointmentBase):
    """Do tworzenia wizyty – wszystkie pola z AppointmentBase są wymagane/ustawiane."""
    pass


class AppointmentUpdate(BaseModel):
    """Do częściowej aktualizacji wizyty – wszystkie pola opcjonalne."""
    visit_datetime: Optional[datetime] = Field(
        None, description="Data i czas wizyty"
    )
    reason: Optional[str] = Field(
        None, description="Powód wizyty lub rodzaj usługi"
    )
    treatment: Optional[str] = Field(
        None, description="Zastosowane leczenie podczas wizyty"
    )
    priority: Optional[str] = Field(
        None, description="Priorytet wizyty"
    )
    weight: Optional[float] = Field(
        None, description="Waga zwierzęcia w dniu wizyty (kg)"
    )
    doctor_id: Optional[int] = Field(
        None, description="ID lekarza obsługującego wizytę"
    )
    animal_id: Optional[int] = Field(
        None, description="ID zwierzęcia będącego pacjentem"
    )
    owner_id: Optional[int] = Field(
        None, description="ID właściciela zwierzęcia"
    )
    notes: Optional[str] = Field(
        None, description="Dodatkowe uwagi"
    )

    model_config = ConfigDict(from_attributes=True)


class Appointment(AppointmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    # w odpowiedziach REST możemy od razu podawać ORM-owe atrybuty:
    model_config = ConfigDict(from_attributes=True)
