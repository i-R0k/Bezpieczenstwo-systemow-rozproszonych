from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox, QLabel
)

from vetclinic_gui.services.facility_service import FacilityService

class CreateFacilityPage(QWidget):
    """
    Ekran tworzenia nowej placówki (przychodni).
    """
    def __init__(self, admin_id=None):
        super().__init__()
        self.admin_id = admin_id
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Nowa placówka")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        layout.addWidget(title)

        form = QFormLayout()
        self.name_le = QLineEdit()
        self.address_le = QLineEdit()
        self.phone_le = QLineEdit()

        form.addRow("Nazwa:", self.name_le)
        form.addRow("Adres:", self.address_le)
        form.addRow("Telefon:", self.phone_le)

        self.create_btn = QPushButton("Utwórz placówkę")
        self.create_btn.clicked.connect(self._on_create)

        layout.addLayout(form)
        layout.addWidget(self.create_btn)

    def _on_create(self):
        payload = {
            "name": self.name_le.text(),
            "address": self.address_le.text(),
            "phone": self.phone_le.text(),
            "created_by": self.admin_id,
        }
        try:
            FacilityService.create(payload)
            QMessageBox.information(self, "Sukces", "Placówka została utworzona.")
            for w in (self.name_le, self.address_le, self.phone_le):
                w.clear()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))
