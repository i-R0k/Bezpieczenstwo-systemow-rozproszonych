import re

def validate_phone_number(value: str) -> str:
    """
    Waliduje numer telefonu – musi zaczynać się od '+' i zawierać od 1 do 3 cyfr kierunkowych oraz co najmniej 6 cyfr numeru.
    Przykład: +48123456789
    """
    if not re.fullmatch(r"\+\d{1,3}\d{6,}", value):
        raise ValueError("Numer telefonu musi zawierać kierunkowy i cyfry, np. +48123456789")
    return value
