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
        r_id, data_hash, timestamp, deleted, owner = blockchain_crud.get_record(record_id)
        if deleted:
            raise HTTPException(status_code=404, detail="Record has been deleted")
        return {
            "id":        r_id,
            "data_hash": data_hash,
            "timestamp": timestamp,
            "owner":     owner
        }
    except HTTPException:
        # przekazujemy już nasze 404 z komunikatem
        raise
    except Exception:
        # np. index out of range, jeżeli kontrakt zwrócił coś innego
        raise HTTPException(status_code=404, detail="Record not found")

@router.get("/blockchain/records-by-owner/{owner_address}")
def get_records_by_owner(owner_address: str):
    """
    Zwraca listę wszystkich ID rekordów zapisanych on-chain przez danego właściciela.
    """
    try:
        ids = blockchain_crud.get_records_by_owner(owner_address)
        # filtrujemy usunięte, jeśli chcesz:
        active_ids = []
        for rec_id in ids:
            _, _, _, deleted, _ = blockchain_crud.get_record(rec_id)
            if not deleted:
                active_ids.append(rec_id)

        return {
            "owner": owner_address,
            "record_ids": active_ids
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
