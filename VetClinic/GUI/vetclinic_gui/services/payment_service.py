import requests

class PaymentService:
    BASE_URL = "http://127.0.0.1:8000"  # Twój backend

    @staticmethod
    def stripe_checkout(invoice_id: int) -> str:
        resp = requests.post(
            f"{PaymentService.BASE_URL}/payments/stripe/{invoice_id}",
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()["url"]

    @staticmethod
    def payu_checkout(invoice_id: int, buyer_email: str, buyer_name: str) -> str:
        resp = requests.post(
            f"{PaymentService.BASE_URL}/payments/payu/{invoice_id}",
            params={"buyer_email": buyer_email, "buyer_name": buyer_name},
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()["redirectUri"]
