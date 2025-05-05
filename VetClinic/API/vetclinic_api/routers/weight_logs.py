# vetclinic_api/routers/weight_logs.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from vetclinic_api.core.database import get_db
from vetclinic_api.schemas.weight_logs import WeightLogCreate, WeightLogOut
from vetclinic_api.crud.weight_log_crud import (
    list_weight_logs,
    get_weight_log,
    create_weight_log,
    delete_weight_log,
)

router = APIRouter(prefix="/weight-logs", tags=["weight-logs"])

@router.get("/", response_model=list[WeightLogOut])
def read_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return list_weight_logs(db, skip, limit)

@router.post("/", response_model=WeightLogOut)
def add_log(schema: WeightLogCreate, db: Session = Depends(get_db)):
    return create_weight_log(db, schema)

@router.get("/{log_id}", response_model=WeightLogOut)
def read_log(log_id: int, db: Session = Depends(get_db)):
    obj = get_weight_log(db, log_id)
    if not obj:
        raise HTTPException(404, "Log nie znaleziony")
    return obj

@router.delete("/{log_id}", response_model=WeightLogOut)
def remove_log(log_id: int, db: Session = Depends(get_db)):
    obj = delete_weight_log(db, log_id)
    if not obj:
        raise HTTPException(404, "Log nie znaleziony")
    return obj
