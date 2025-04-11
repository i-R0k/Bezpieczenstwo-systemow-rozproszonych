"""
Router do obsługi endpointów związanych z fakturami.
"""

from fastapi import APIRouter

router = APIRouter(
    prefix="/invoices",
    tags=["invoices"],
)

@router.get("/")
def read_invoices():
    return {"invoices": []}
