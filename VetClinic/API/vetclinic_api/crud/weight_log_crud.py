# vetclinic_api/crud/weight_log_crud.py

from sqlalchemy.orm import Session
from vetclinic_api.models.weight_logs import WeightLog as WeightLogModel
from vetclinic_api.schemas.weight_logs import WeightLogCreate

def list_weight_logs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(WeightLogModel).offset(skip).limit(limit).all()

def get_weight_log(db: Session, log_id: int):
    return db.query(WeightLogModel).filter(WeightLogModel.id == log_id).first()

def create_weight_log(db: Session, schema: WeightLogCreate):
    # schema.recorded_at może być None, baza ustawi teraz
    data = schema.model_dump(exclude_unset=True)
    db_obj = WeightLogModel(**data)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_weight_log(db: Session, log_id: int):
    obj = db.query(WeightLogModel).get(log_id)
    if obj:
        db.delete(obj)
        db.commit()
    return obj
