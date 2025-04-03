import re

def validate_letters(value: str) -> str:
    """
    Waliduje, że wartość zawiera tylko litery (w tym polskie znaki) i opcjonalne spacje.
    """
    if not re.fullmatch(r"[A-Za-ząćęłńóśźżĄĆĘŁŃÓŚŹŻ]+(?:\s+[A-Za-ząćęłńóśźżĄĆĘŁŃÓŚŹŻ]+)*", value):
        raise ValueError("Pole musi zawierać tylko litery i opcjonalnie spacje")
    return value
