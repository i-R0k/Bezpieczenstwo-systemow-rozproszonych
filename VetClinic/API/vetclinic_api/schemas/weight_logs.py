from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime

class WeightLogBase(BaseModel):
    animal_id: int = Field(..., description="ID zwierzęcia")
    weight: float  = Field(..., gt=0, description="Waga zwierzęcia w kg")
    recorded_at: datetime | None = Field(
        None,
        description="Data i czas pomiaru; domyślnie ustawiana przez bazę"
    )

    model_config = ConfigDict(from_attributes=True)

    @field_validator("weight")
    def validate_weight(cls, v):
        if v <= 0:
            raise ValueError("Waga musi być większa od zera")
        return v

class WeightLogCreate(WeightLogBase):
    # przy tworzeniu nie podajemy recorded_at – baza ustawi func.now()
    recorded_at: datetime | None = None

class WeightLogOut(WeightLogBase):
    id: int = Field(..., description="ID rekordu")
