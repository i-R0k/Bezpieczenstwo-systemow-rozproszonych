import re

def validate_postal_code(value: str) -> str:
    """
    Waliduje kod pocztowy. Spodziewany format: "XX-XXX Miejscowość"
    Gdzie:
      - XX-XXX: dokładnie 2 cyfry, myślnik i 3 cyfry,
      - Miejscowość: ciąg liter (może zawierać spacje)
    Przykład: "00-001 Warszawa"
    """
    
    pattern = r"^\d{2}-\d{3}\s+[A-Za-ząćęłńóśźżĄĆĘŁŃÓŚŹŻ]+(?:\s+[A-Za-ząćęłńóśźżĄĆĘŁŃÓŚŹŻ]+)*$"
    if not re.fullmatch(pattern, value):
        raise ValueError("Kod pocztowy musi być w formacie 'XX-XXX Miejscowość', np. '00-001 Warszawa'")
    return value
