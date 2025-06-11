# vetclinic_api/schemas/invoice.py

from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field

class InvoiceCreate(BaseModel):
    client_id: int
    amount: Decimal = Field(
        ...,
        max_digits=10,
        decimal_places=2,
        gt=0
    )

class InvoiceRead(BaseModel):
    id: int
    client_id: int
    amount: Decimal = Field(
        ...,
        max_digits=10,
        decimal_places=2
    )
    status: str
    created_at: datetime

    class Config:
        orm_mode = True
