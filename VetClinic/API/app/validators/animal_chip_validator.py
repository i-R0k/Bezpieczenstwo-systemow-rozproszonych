import re

def validate_animal_chip(chip_number: str) -> bool:
    """
    Sprawdza, czy podany numer mikroczipa spełnia standardowy format 15 cyfr.

    Args:
        chip_number (str): Numer mikroczipa do walidacji.

    Returns:
        bool: True, jeśli chip_number składa się dokładnie z 15 cyfr,
              False w przeciwnym wypadku.
    """
    pattern = r'^\d{15}$'
    return bool(re.match(pattern, chip_number))

