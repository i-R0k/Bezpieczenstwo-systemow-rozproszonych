# vetclinic_gui/services/weight_logs_service.py

from vetclinic_gui.services.db import SessionLocal
from vetclinic_api.crud.weight_log_crud import list_weight_logs
from typing import List

class WeightLogService:
    @staticmethod
    def list_by_animal(animal_id: int, skip: int = 0, limit: int = 100) -> List:
        db = SessionLocal()
        try:
            # pobieramy wszystkie logi, a następnie filtrujemy po animal_id
            logs = list_weight_logs(db, skip=skip, limit=limit)
            return [wl for wl in logs if getattr(wl, "animal_id", None) == animal_id]
        finally:
            db.close()

# alias
WeightLogService = WeightLogService
