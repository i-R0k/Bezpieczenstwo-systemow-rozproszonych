class ConsultantService:
    @staticmethod
    def list() -> List[User]:
        """Pobiera wszystkich konsultantów (role='consultant')."""
    @staticmethod
    def get(user_id: int) -> User:
        """Szczegóły konsultanta."""
    @staticmethod
    def create(payload: dict) -> User:
        """Tworzy nowego konsultanta."""
    @staticmethod
    def update(user_id: int, payload: dict) -> User:
        """Modyfikuje dane konsultanta."""
    @staticmethod
    def deactivate(user_id: int) -> None:
        """Dezaktywuje konsultanta (lub usuwa)."""
