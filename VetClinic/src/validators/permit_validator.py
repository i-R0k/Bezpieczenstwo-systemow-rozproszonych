import re

def validate_permit_number(value: str) -> str:
    """
    Waliduje numer pozwolenia – musi składać się z dokładnie 5 cyfr.
    """
    if not re.fullmatch(r"\d{5}", value):
        raise ValueError("Numer pozwolenia musi składać się z dokładnie 5 cyfr")
    return value
