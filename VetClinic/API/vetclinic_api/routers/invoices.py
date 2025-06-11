from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from vetclinic_api.schemas.invoice import InvoiceCreate, InvoiceRead
from vetclinic_api.crud.invoice_crud import create_invoice, get_invoice, list_invoices, update_invoice_status
from vetclinic_api.core.database import get_db

router = APIRouter(prefix="/invoices", tags=["invoices"])

@router.post("/", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def api_create_invoice(inv: InvoiceCreate, db: Session = Depends(get_db)):
    return create_invoice(db, inv)

@router.get("/", response_model=List[InvoiceRead])
def api_list_invoices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return list_invoices(db, skip, limit)

@router.get("/{invoice_id}", response_model=InvoiceRead)
def api_get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = get_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return inv

@router.patch("/{invoice_id}/status", response_model=InvoiceRead)
def api_update_invoice_status(invoice_id: int, status: str, db: Session = Depends(get_db)):
    inv = update_invoice_status(db, invoice_id, status)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return inv
