import sys
import json
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QMessageBox
)

API_LOGIN_URL = "http://127.0.0.1:8000/users/login"  # Zakładamy, że endpoint logowania jest tu dostępny

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logowanie - VetClinic")
        self.setup_ui()

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

        self.login_button = QPushButton("Zaloguj się")
        self.login_button.clicked.connect(self.login)

        self.status_label = QLabel("")

        layout.addLayout(form_layout)
        layout.addWidget(self.login_button)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    def login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not email or not password:
            QMessageBox.warning(self, "Błąd", "Wprowadź email oraz hasło.")
            return

        # Przygotuj dane do wysłania
        payload = {"email": email, "password": password}
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(API_LOGIN_URL, data=json.dumps(payload), headers=headers)
            if response.status_code == 200:
                # Jeśli logowanie się uda, możesz np. wyświetlić komunikat sukcesu
                QMessageBox.information(self, "Sukces", "Logowanie powiodło się!")
                self.status_label.setText("Zalogowano pomyślnie.")
                # Tutaj możesz wywołać kolejne okno lub zapisać token sesji, itp.
            else:
                QMessageBox.warning(self, "Błąd", f"Logowanie nie powiodło się: {response.text}")
                self.status_label.setText("Błąd logowania.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się połączyć z API: {e}")
            self.status_label.setText("Błąd połączenia z API.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
