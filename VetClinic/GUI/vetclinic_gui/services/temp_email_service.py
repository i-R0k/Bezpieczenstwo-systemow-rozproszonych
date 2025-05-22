import requests

BASE_URL = "https://api.mail.gw"

class TempEmailService:

    @staticmethod
    def get_domain() -> str:
        """
        Zwraca pierwszą dostępną domenę z API mail.gw.
        """
        r = requests.get(f"{BASE_URL}/domains")
        r.raise_for_status()
        domains = r.json().get("hydra:member", [])
        if not domains:
            raise RuntimeError("Brak dostępnych domen dla tymczasowego e-maila")
        return domains[0]["domain"]
