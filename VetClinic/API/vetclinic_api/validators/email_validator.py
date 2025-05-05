from pydantic import EmailStr

def validate_email(email: EmailStr, role: str) -> EmailStr:
    """
    Waliduje adres e-mail na podstawie roli użytkownika:
      - Jeśli rola to "doctor", e-mail musi kończyć się na "@lekarz.vetclinic.com"
      - Jeśli rola to "konsultant", e-mail musi kończyć się na "@konsultant.vetclinic.com"
      - Dla klientów (role "klient") nie stosujemy specjalnego ograniczenia.
    """
    if role == "lekarz":
        if not email.endswith("@lekarz.vetclinic.com"):
            raise ValueError("Email dla lekarza musi kończyć się na @lekarz.vetclinic.com")
    elif role == "konsultant":
        if not email.endswith("@konsultant.vetclinic.com"):
            raise ValueError("Email dla konsultanta musi kończyć się na @konsultant.vetclinic.com")
    # Dla klientów nie wykonujemy dodatkowej walidacji.
    return email
