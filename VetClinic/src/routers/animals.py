"""
Router do obsługi endpointów związanych z zarządzaniem danymi zwierząt.
"""

from fastapi import APIRouter

router = APIRouter(
    prefix="/animals",
    tags=["animals"],
)

@router.get("/")
def read_animals():
    return {"animals": []}
