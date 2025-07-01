import requests

class AuthService:
    """Wywołania HTTP dla login/change-password/confirm-totp."""
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base = base_url.rstrip("/")

    def login(self, email: str, password: str, otp_code: str = None, totp_code: str = None):
        payload = {"email": email, "password": password}
        if otp_code:
            payload["otp_code"] = otp_code
        if totp_code:
            payload["totp_code"] = totp_code
        return requests.post(f"{self.base}/users/login", json=payload)

    def confirm_totp(self, email: str, totp_code: str):
        return requests.post(
            f"{self.base}/users/confirm-totp",
            json={"email": email, "totp_code": totp_code}
        )

    def change_password(self, email: str, old_password: str, new_password: str, reset_totp: bool = False):
        return requests.post(
            f"{self.base}/users/change-password",
            json={
                "email": email,
                "old_password": old_password,
                "new_password": new_password,
                "reset_totp": reset_totp
            }
        )

    def setup_totp(self, email: str):
        return requests.post(f"{self.base}/users/setup-totp", params={"email": email})
