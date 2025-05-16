class FacilityService:
    @staticmethod
    def list() -> List[Facility]:
        """Pobiera wszystkie placówki."""
    @staticmethod
    def get(facility_id: int) -> Facility:
        """Szczegóły pojedynczej placówki."""
    @staticmethod
    def create(payload: dict) -> Facility:
        """Tworzy nową placówkę."""
    @staticmethod
    def update(facility_id: int, payload: dict) -> Facility:
        """Aktualizuje istniejącą placówkę."""
    @staticmethod
    def delete(facility_id: int) -> None:
        """Usuwa placówkę."""
