from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from vetclinic_api.crud import blockchain_crud

router = APIRouter()

class BlockchainRecord(BaseModel):
    id: int
    data_hash: str

@router.post("/blockchain/record")
def add_blockchain_record(record: BlockchainRecord):
    try:
        tx_hash = blockchain_crud.add_record(record.id, record.data_hash)
        return {"status": "ok", "tx_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blockchain/record/{record_id}")
def get_blockchain_record(record_id: int):
    try:
        r_id, data_hash, timestamp = blockchain_crud.get_record(record_id)
        return {"id": r_id, "data_hash": data_hash, "timestamp": timestamp}
    except Exception:
        raise HTTPException(status_code=404, detail="Record not found")

@router.put("/blockchain/record/{record_id}")
def update_record(record_id: int, data: BlockchainRecord):
    try:
        tx_hash = blockchain_crud.update_record(record_id, data.data_hash)
        return {"status": "updated", "tx_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/blockchain/record/{record_id}")
def delete_record(record_id: int):
    try:
        tx_hash = blockchain_crud.delete_record(record_id)
        return {"status": "deleted", "tx_hash": tx_hash}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
