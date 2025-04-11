"""
Router do obsługi endpointów historii leczenia.
"""

from fastapi import APIRouter

router = APIRouter(
    prefix="/medical_records",
    tags=["medical_records"],
)

@router.get("/")
def read_medical_records():
    return {"medical_records": []}
