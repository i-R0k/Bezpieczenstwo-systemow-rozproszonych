from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class MedicalRecordBase(BaseModel):
    animal_id: int
    description: str
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None

class MedicalRecordCreate(MedicalRecordBase):
    pass

class MedicalRecordUpdate(BaseModel):
    description: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment: Optional[str] = None

class MedicalRecord(MedicalRecordBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)