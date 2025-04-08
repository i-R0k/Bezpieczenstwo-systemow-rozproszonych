import sys
import json
import io
import requests
import qrcode
import pyotp

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QMessageBox, QDialog
)
from PyQt5.QtGui import QPixmap, QImage

# Adresy endpointów API – dostosuj je do swojej konfiguracji
API_LOGIN_URL = "http://127.0.0.1:8000/users/login"
API_CONFIRM_TOTP_URL = "http://127.0.0.1:8000/users/confirm-totp"

class SetupTOTPDialog(QDialog):
    """
    Okno dialogowe służące do konfiguracji TOTP.
    Wyświetla QR Code, który użytkownik skanuje w Google Authenticator oraz pole do wpisania
    wygenerowanego 6-cyfrowego kodu.
    """
    def __init__(self, totp_uri, email):
        super().__init__()
        self.totp_uri = totp_uri
        self.email = email
        self.setWindowTitle("Konfiguracja TOTP")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Etykieta z informacją
        label_info = QLabel("Zeskanuj poniższy kod QR w Google Authenticator, a następnie wpisz wygenerowany kod:")
        layout.addWidget(label_info)

        # Widżet do wyświetlania QR Code
        self.qr_label = QLabel()
        layout.addWidget(self.qr_label)
        self.generate_qr(self.totp_uri)

        # Pole do wpisania kodu TOTP
        self.totp_input = QLineEdit()
        self.totp_input.setPlaceholderText("Wpisz 6-cyfrowy kod TOTP")
        self.totp_input.setMaxLength(6)
        layout.addWidget(self.totp_input)

        # Przycisk potwierdzenia
        self.confirm_button = QPushButton("Potwierdź TOTP")
        self.confirm_button.clicked.connect(self.confirm_totp)
        layout.addWidget(self.confirm_button)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.resize(350, 450)

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
        # Konwersja obrazu PIL do QPixmap
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qimg = QImage()
        qimg.loadFromData(buf.getvalue(), "PNG")
        pixmap = QPixmap.fromImage(qimg)
        self.qr_label.setPixmap(pixmap)
        self.qr_label.setScaledContents(True)

    def confirm_totp(self):
        totp_code = self.totp_input.text().strip()
        if not totp_code:
            QMessageBox.warning(self, "Błąd", "Wprowadź kod TOTP!")
            return
        payload = {"email": self.email, "totp_code": totp_code}
        try:
            response = requests.post(API_CONFIRM_TOTP_URL, json=payload)
            if response.status_code == 200:
                QMessageBox.information(self, "Sukces", "TOTP skonfigurowany pomyślnie!")
                self.accept()  # Zamyka dialog – konfiguracja TOTP zakończona
            else:
                detail = response.json().get("detail", "Błąd potwierdzenia TOTP")
                QMessageBox.warning(self, "Błąd", f"Nie udało się potwierdzić TOTP: {detail}")
                self.status_label.setText("Błąd potwierdzenia TOTP.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Problem z połączeniem: {e}")
            self.status_label.setText("Błąd połączenia z API.")

class LoginWindow(QWidget):
    """
    Główne okno logowania. Początkowo wyświetla pola:
      - Email
      - Hasło
    Jeśli backend odpowie, że TOTP nie jest skonfigurowany, otwierane jest dodatkowe okno dialogowe
    umożliwiające konfigurację TOTP.
    
    W kolejnych logowaniach, gdy TOTP jest już skonfigurowane, zamiast otwierać dialog, można
    dynamicznie rozszerzyć okno logowania o pole TOTP.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logowanie - VetClinic")
        self.totp_configured = False  # Flaga, czy TOTP jest skonfigurowany
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout()
        self.form_layout = QFormLayout()

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Wprowadź email")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Wprowadź hasło")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.form_layout.addRow("Email:", self.email_input)
        self.form_layout.addRow("Hasło:", self.password_input)

        # Pole na kod TOTP – domyślnie ukryte (jeśli TOTP nie jest skonfigurowany)
        self.totp_input = QLineEdit()
        self.totp_input.setPlaceholderText("Wprowadź 6-cyfrowy kod TOTP")
        self.totp_input.setMaxLength(6)
        self.totp_input.setVisible(False)
        self.form_layout.addRow("Kod TOTP:", self.totp_input)

        self.layout.addLayout(self.form_layout)

        self.login_button = QPushButton("Zaloguj się")
        self.login_button.clicked.connect(self.attempt_login)
        self.layout.addWidget(self.login_button)

        self.status_label = QLabel("")
        self.layout.addWidget(self.status_label)

        self.setLayout(self.layout)

    def attempt_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        totp_code = self.totp_input.text().strip() if self.totp_input.isVisible() else None

        if not email or not password:
            QMessageBox.warning(self, "Błąd", "Wprowadź email i hasło.")
            return

        # Przygotowujemy payload – w pierwszym kroku TOTP może być pominięte
        payload = {"email": email, "password": password}
        if totp_code:
            payload["totp_code"] = totp_code

        try:
            response = requests.post(API_LOGIN_URL, json=payload)
            if response.status_code == 200:
                # Logowanie udane
                QMessageBox.information(self, "Sukces", "Zalogowano pomyślnie!")
                self.status_label.setText("Zalogowano pomyślnie.")
            elif response.status_code == 201:
                # Otrzymujemy provisioning URI – TOTP nie jest skonfigurowany
                data = response.json()
                totp_uri = data.get("totp_uri")
                if totp_uri:
                    # Otwieramy okno dialogowe, aby skonfigurować TOTP
                    dialog = SetupTOTPDialog(totp_uri, email)
                    dialog.exec_()
                    # Po zatwierdzeniu konfiguracji, przełączamy UI,
                    # żeby przy kolejnych logowaniach pole totp było widoczne
                    self.totp_input.setVisible(True)
                    self.status_label.setText("TOTP skonfigurowany, spróbuj ponownie.")
                else:
                    QMessageBox.warning(self, "Błąd", "Brak provisioning URI od API.")
            elif response.status_code == 400 and "TOTP code required" in response.json().get("detail", ""):
                # Jeśli backend zgłasza, że potrzebny jest TOTP, ujawniamy pole do jego wpisania
                self.totp_input.setVisible(True)
                QMessageBox.warning(self, "TOTP", "Wpisz kod TOTP, który generuje Google Authenticator.")
                self.status_label.setText("Wpisz kod TOTP.")
            else:
                detail = response.json().get("detail", "Błąd logowania")
                QMessageBox.warning(self, "Błąd", f"Logowanie nie powiodło się: {detail}")
                self.status_label.setText("Błąd logowania.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się połączyć z API: {e}")
            self.status_label.setText("Błąd połączenia z API.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())
