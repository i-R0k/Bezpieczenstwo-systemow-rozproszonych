import smtplib
from email.mime.text import MIMEText
from vetclinic_api.core.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM

class EmailService:
    @staticmethod
    def send_temporary_password(to_address: str, raw_password: str):
        msg = MIMEText(f"Twoje tymczasowe hasło:\n\n{raw_password}")
        msg["Subject"] = "VetClinic – dane dostępu"
        msg["From"]    = SMTP_FROM
        msg["To"]      = to_address

        # Debug: wypisz co próbujesz połączyć
        print(f"[DEBUG SMTP] host={SMTP_HOST!r} port={SMTP_PORT!r}")

        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.set_debuglevel(1)    # w konsoli zobaczysz SMTP dialog
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
