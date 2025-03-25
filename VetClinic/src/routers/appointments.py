"""
Router do obsługi endpointów związanych z wizytami.
Przykładowy szkielet – rozszerz według potrzeb.
"""

from fastapi import APIRouter

router = APIRouter(
    prefix="/appointments",
    tags=["appointments"],
)

@router.get("/")
def read_appointments():
    # Przykładowa implementacja – zwraca pustą listę
    return {"appointments": []}
