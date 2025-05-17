from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class FacilityBase(BaseModel):
    name: str
    address: str
    phone: Optional[str] = None

class FacilityCreate(FacilityBase):
    pass

class FacilityUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None

class FacilityRead(FacilityBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
