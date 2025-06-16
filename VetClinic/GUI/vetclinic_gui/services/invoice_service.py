from vetclinic_gui.services.db import SessionLocal
from vetclinic_api.crud.invoice_crud import list_invoices

class InvoiceService:
    @staticmethod
    def list_by_client(client_id: int):
        db = SessionLocal()
        try:
            # pobieramy wszystkie faktury i filtrujemy po client_id
            return [inv for inv in list_invoices(db) if inv.client_id == client_id]
        finally:
            db.close()
