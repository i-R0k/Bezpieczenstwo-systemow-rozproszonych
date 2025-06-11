from sqlalchemy.orm import Session
from vetclinic_api.models.invoice import Invoice as InvoiceModel
from vetclinic_api.schemas.invoice import InvoiceCreate

def create_invoice(db: Session, inv: InvoiceCreate) -> InvoiceModel:
    db_inv = InvoiceModel(client_id=inv.client_id, amount=inv.amount)
    db.add(db_inv)
    db.commit()
    db.refresh(db_inv)
    return db_inv

def get_invoice(db: Session, invoice_id: int) -> InvoiceModel | None:
    return db.query(InvoiceModel).filter(InvoiceModel.id == invoice_id).first()

def list_invoices(db: Session, skip: int = 0, limit: int = 100) -> list[InvoiceModel]:
    return db.query(InvoiceModel).offset(skip).limit(limit).all()

def update_invoice_status(db: Session, invoice_id: int, new_status: str) -> InvoiceModel | None:
    inv = get_invoice(db, invoice_id)
    if not inv:
        return None
    inv.status = new_status
    db.commit()
    db.refresh(inv)
    return inv
