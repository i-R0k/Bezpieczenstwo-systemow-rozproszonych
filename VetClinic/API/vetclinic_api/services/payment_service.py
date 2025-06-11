import stripe
import os

stripe.api_key = os.getenv("STRIPE_API_KEY", "")

def create_stripe_session(invoice_id: int, amount: float):
    """
    Tworzy Stripe Checkout Session w trybie sandbox.
    """
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": f"Invoice #{invoice_id}"},
                "unit_amount": int(amount * 100),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=os.getenv("SUCCESS_URL"),
        cancel_url=os.getenv("CANCEL_URL"),
    )
    return session
