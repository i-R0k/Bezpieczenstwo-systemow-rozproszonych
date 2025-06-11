from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from vetclinic_api.services.payment_service import create_stripe_session
from vetclinic_api.services.payu_service import create_payu_order
from vetclinic_api.crud.invoice_crud import get_invoice
from vetclinic_api.core.database import get_db

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/stripe/{invoice_id}")
def api_stripe_session(invoice_id: int, db: Session = Depends(get_db)):
    inv = get_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    session = create_stripe_session(invoice_id, float(inv.amount))
    return {"provider": "stripe", "session_id": session.id, "url": session.url}

@router.post("/payu/{invoice_id}")
def api_payu_order(invoice_id: int, buyer_email: str, buyer_name: str, db: Session = Depends(get_db)):
    inv = get_invoice(db, invoice_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    order = create_payu_order(invoice_id, float(inv.amount), buyer_email, buyer_name)
    return {
        "provider": "payu",
        "orderId": order["orderId"],
        "redirectUri": order["redirectUri"]
    }
