from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox, QLabel
)

from vetclinic_gui.services.users_service import UserService

class CreateConsultantPage(QWidget):
    """
    Ekran tworzenia nowego konsultanta.
    """
    def __init__(self, admin_id=None):
        super().__init__()
        self.admin_id = admin_id
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Nowy konsultant")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        layout.addWidget(title)

        form = QFormLayout()
        self.first_name_le = QLineEdit()
        self.last_name_le = QLineEdit()
        self.email_le = QLineEdit()
        self.phone_le = QLineEdit()

        form.addRow("Imię:", self.first_name_le)
        form.addRow("Nazwisko:", self.last_name_le)
        form.addRow("Email:", self.email_le)
        form.addRow("Telefon:", self.phone_le)

        self.create_btn = QPushButton("Dodaj konsultanta")
        self.create_btn.clicked.connect(self._on_create)

        layout.addLayout(form)
        layout.addWidget(self.create_btn)

    def _on_create(self):
        payload = {
            "first_name": self.first_name_le.text(),
            "last_name": self.last_name_le.text(),
            "email": self.email_le.text(),
            "phone": self.phone_le.text(),
            "role": "consultant",
            "created_by": self.admin_id,
        }
        try:
            UserService.create(payload)
            QMessageBox.information(self, "Sukces", "Konsultant został dodany.")
            for w in (self.first_name_le, self.last_name_le, self.email_le, self.phone_le):
                w.clear()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))
