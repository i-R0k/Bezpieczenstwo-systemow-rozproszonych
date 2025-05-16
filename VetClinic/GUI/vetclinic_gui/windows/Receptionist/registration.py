from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QLabel,
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem
)
from datetime import datetime

from vetclinic_gui.services.clients_service import UserService
from vetclinic_gui.services.appointments_service import AppointmentService

class RegistrationPage(QWidget):
    """
    Ekran do rejestracji nowego użytkownika (właściciela zwierzęcia).
    """
    def __init__(self, receptionist_id=None):
        super().__init__()
        self.receptionist_id = receptionist_id
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.first_name_le = QLineEdit()
        self.last_name_le = QLineEdit()
        self.phone_le = QLineEdit()
        self.email_le = QLineEdit()
        self.address_le = QLineEdit()

        form.addRow("Imię:", self.first_name_le)
        form.addRow("Nazwisko:", self.last_name_le)
        form.addRow("Telefon:", self.phone_le)
        form.addRow("Email:", self.email_le)
        form.addRow("Adres:", self.address_le)

        self.register_btn = QPushButton("Zarejestruj użytkownika")
        self.register_btn.clicked.connect(self._on_register)

        layout.addLayout(form)
        layout.addWidget(self.register_btn)

    def _on_register(self):
        payload = {
            "first_name": self.first_name_le.text(),
            "last_name":  self.last_name_le.text(),
            "phone":      self.phone_le.text(),
            "email":      self.email_le.text(),
            "address":    self.address_le.text(),
        }
        try:
            UserService.create(payload)
            QMessageBox.information(self, "Sukces", "Użytkownik został zarejestrowany.")
            for w in [
                self.first_name_le, self.last_name_le,
                self.phone_le, self.email_le, self.address_le
            ]:
                w.clear()
        except Exception as e:
            QMessageBox.critical(self, "Błąd rejestracji", str(e))

class ReceptionistDashboardPage(QWidget):
    """
    Dashboard recepcjonisty - przegląd nadchodzących wizyt.
    """
    def __init__(self, receptionist_id=None):
        super().__init__()
        self.receptionist_id = receptionist_id
        self._setup_ui()
        self._load_upcoming_visits()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Nadchodzące wizyty")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        layout.addWidget(title)

        self.visits_table = QTableWidget(0, 4)
        self.visits_table.setHorizontalHeaderLabels([
            "Data", "Godzina", "Gabinet", "Lekarz"
        ])
        layout.addWidget(self.visits_table)

    def _load_upcoming_visits(self):
        all_visits = AppointmentService.list()
        now = datetime.now()
        upcoming = []
        for v in all_visits:
            try:
                dt = datetime.fromisoformat(v.visit_datetime)
            except Exception:
                continue
            if dt >= now:
                upcoming.append((dt, v))

        upcoming.sort(key=lambda x: x[0])
        self.visits_table.setRowCount(0)

        for dt, v in upcoming:
            row = self.visits_table.rowCount()
            self.visits_table.insertRow(row)
            date_str = dt.date().isoformat()
            time_str = dt.strftime("%H:%M")

            room = next((r for r in AppointmentService._rooms if getattr(r, 'id', None) == v.room_id), None)
            room_name = getattr(room, 'name', '') if room else ''

            doctor = next((d for d in AppointmentService._doctors if getattr(d, 'id', None) == v.doctor_id), None)
            doctor_name = f"{doctor.first_name} {doctor.last_name}" if doctor else ''

            values = [date_str, time_str, room_name, doctor_name]
            for col, val in enumerate(values):
                self.visits_table.setItem(row, col, QTableWidgetItem(val))
