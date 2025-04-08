import sys
import json
import io
import requests
import qrcode
import pyotp

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage

API_LOGIN_URL = "http://127.0.0.1:8000/users/login"
API_SETUP_TOTP_URL = "http://127.0.0.1:8000/users/setup-totp"
API_CONFIRM_TOTP_URL = "http://127.0.0.1:8000/users/confirm-totp"

class SetupTOTPWindow(QWidget):
    """
    Okno, w którym użytkownik skanuje QR code
    i wpisuje wygenerowany kod TOTP, aby go potwierdzić.
    """
    def __init__(self, email: str, totp_uri: str):
        super().__init__()
        self.email = email
        self.totp_uri = totp_uri
        self.setWindowTitle("Skonfiguruj TOTP")
        self.layout = QVBoxLayout()
        
        # Wyświetlanie QR code
        self.qr_label = QLabel("Zeskanuj kod w Google Authenticator:")
        self.layout.addWidget(self.qr_label)
        
        self.qr_image_label = QLabel()
        self.layout.addWidget(self.qr_image_label)
        self.generate_qr(totp_uri)
        
        # Pole do wpisania kodu TOTP
        self.totp_input = QLineEdit()
        self.totp_input.setPlaceholderText("Wpisz kod TOTP z Google Authenticator")
        self.totp_input.setMaxLength(6)
        self.layout.addWidget(self.totp_input)
        
        # Przycisk zatwierdzenia kodu
        self.confirm_button = QPushButton("Zatwierdź")
        self.confirm_button.clicked.connect(self.confirm_totp)
        self.layout.addWidget(self.confirm_button)
        
        self.status_label = QLabel("")
        self.layout.addWidget(self.status_label)
        
        self.setLayout(self.layout)
    
    def generate_qr(self, totp_uri):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qimg = QImage()
        qimg.loadFromData(buf.getvalue(), "PNG")
        pixmap = QPixmap.fromImage(qimg)
        self.qr_image_label.setPixmap(pixmap)
        self.qr_image_label.setScaledContents(True)
        self.resize(400, 400)
    
    def confirm_totp(self):
        """
        Wysyłamy kod TOTP do API w celu potwierdzenia.
        """
        totp_code = self.totp_input.text().strip()
        if not totp_code:
            QMessageBox.warning(self, "Błąd", "Wpisz kod TOTP.")
            return
        
        payload = {"email": self.email, "totp_code": totp_code}
        try:
            response = requests.post(API_CONFIRM_TOTP_URL, json=payload)
            if response.status_code == 200:
                QMessageBox.information(self, "Sukces", "TOTP skonfigurowany pomyślnie!")
                self.status_label.setText("TOTP potwierdzony.")
                self.close()  # Możesz zamknąć to okno po potwierdzeniu
            else:
                detail = response.json().get("detail", "")
                QMessageBox.warning(self, "Błąd", f"Nie udało się potwierdzić TOTP: {detail}")
                self.status_label.setText("Błąd potwierdzenia TOTP.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Problem z połączeniem do API: {e}")
            self.status_label.setText("Błąd połączenia z API.")


class LoginWindow(QWidget):
    """
    Główne okno logowania.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logowanie - VetClinic")
        self.setup_ui()
        self.totp_window = None

    def setup_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Wprowadź email")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Wprowadź hasło")
        self.password_input.setEchoMode(QLineEdit.Password)

        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Hasło:", self.password_input)

        layout.addLayout(form_layout)

        self.login_button = QPushButton("Zaloguj się")
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not email or not password:
            QMessageBox.warning(self, "Błąd", "Wpisz email oraz hasło.")
            return

        payload = {"email": email, "password": password}
        try:
            response = requests.post(API_LOGIN_URL, json=payload)
            if response.status_code == 200:
                # Zwrócony token lub info, że TOTP jest już skonfigurowany i oczekuje kodu
                data = response.json()
                # Jeżeli logowanie wymaga TOTP:
                # - API może zwrócić np. "need_totp": True/False
                if data.get("need_totp") is True:
                    # Możesz wyświetlić kolejne okno z polem TOTP, 
                    # lub generować TOTP na serwerze i wysyłać weryfikację
                    QMessageBox.information(self, "TOTP", "Podaj kod TOTP w kolejnym kroku.")
                    # Tutaj możesz otworzyć drugie okno do wprowadzenia kodu TOTP
                    # Ale w Twoim scenariuszu jest inaczej – najpierw generujemy QR code?
                    # Zależnie od logiki API – trzeba zdecydować, czy user już ma TOTP, czy nie.
                else:
                    QMessageBox.information(self, "Sukces", "Zalogowano pomyślnie bez TOTP.")
                self.status_label.setText("Zalogowano pomyślnie.")
            elif response.status_code == 201:
                # Możliwe, że API zwraca 201 i provisioning URI do TOTP
                # Generujemy okno QR code i prosimy usera o wprowadzenie kodu
                data = response.json()
                totp_uri = data.get("totp_uri")
                if totp_uri:
                    self.totp_window = SetupTOTPWindow(self.email_input.text(), totp_uri)
                    self.totp_window.show()
                else:
                    QMessageBox.warning(self, "Błąd", "Brak totp_uri w odpowiedzi API.")
            else:
                detail = response.json().get("detail", "")
                QMessageBox.warning(self, "Błąd", f"Logowanie nie powiodło się: {detail}")
                self.status_label.setText("Błąd logowania.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się połączyć z API: {e}")
            self.status_label.setText("Błąd połączenia z API.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
