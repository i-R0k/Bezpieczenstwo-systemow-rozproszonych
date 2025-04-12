from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field

class AnimalBase(BaseModel):
    name: str = Field(..., description="Imię zwierzęcia")
    species: str = Field(..., description="Gatunek, np. pies, kot")
    breed: Optional[str] = Field(None, description="Rasa zwierzęcia")
    gender: Optional[str] = Field(None, description="Płeć zwierzęcia, np. male lub female")
    birth_date: Optional[date] = Field(None, description="Data urodzenia zwierzęcia")
    age: Optional[int] = Field(None, description="Wiek zwierzęcia (opcjonalnie)")
    weight: Optional[float] = Field(None, description="Waga zwierzęcia w kg")
    microchip_number: Optional[str] = Field(None, description="Numer mikroczipa")
    notes: Optional[str] = Field(None, description="Dodatkowe uwagi")
    owner_id: int = Field(..., description="ID właściciela zwierzęcia")
    last_visit: Optional[datetime] = Field(None, description="Data ostatniej wizyty u weterynarza")

class AnimalCreate(AnimalBase):
    pass

class AnimalUpdate(BaseModel):
    # Umożliwiamy aktualizację wybranych pól – używamy Optional
    name: Optional[str] = Field(None, description="Imię zwierzęcia")
    species: Optional[str] = Field(None, description="Gatunek")
    breed: Optional[str] = Field(None, description="Rasa")
    gender: Optional[str] = Field(None, description="Płeć")
    birth_date: Optional[date] = Field(None, description="Data urodzenia")
    age: Optional[int] = Field(None, description="Wiek")
    weight: Optional[float] = Field(None, description="Waga w kg")
    microchip_number: Optional[str] = Field(None, description="Numer mikroczipa")
    notes: Optional[str] = Field(None, description="Uwagi")
    owner_id: Optional[int] = Field(None, description="ID właściciela")
    last_visit: Optional[datetime] = Field(None, description="Data ostatniej wizyty")

class Animal(AnimalBase):
    id: int = Field(..., description="Unikalny identyfikator")
    created_at: datetime = Field(..., description="Data utworzenia rekordu")
    updated_at: datetime = Field(..., description="Data ostatniej modyfikacji")

    class Config:
        form_attributes = True
