from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel,
    QPushButton, QMessageBox, QComboBox,
    QDateEdit, QTimeEdit, QCheckBox, QLineEdit
)
from PyQt5.QtCore import QDate, QTime
from datetime import datetime

from vetclinic_gui.services.clients_service import ClientService
from vetclinic_gui.services.animals_service import AnimalService
from vetclinic_gui.services.doctors_service import DoctorService
from vetclinic_gui.services.appointments_service import AppointmentService

class ScheduleVisitPage(QWidget):
    """
    Ekran umawiania wizyt: klient, zwierzę, lekarz, data, godzina, pilne, powód.
    """
    def __init__(self, receptionist_id=None):
        super().__init__()
        self.receptionist_id = receptionist_id
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Umawianie wizyty")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        layout.addWidget(title)

        form = QFormLayout()

        # Wybór klienta
        self.client_cb = QComboBox()
        self.clients = ClientService.list()
        for client in self.clients:
            self.client_cb.addItem(f"{client.first_name} {client.last_name}", client.id)
        self.client_cb.currentIndexChanged.connect(self._on_client_changed)
        form.addRow("Klient:", self.client_cb)

        # Wybór zwierzęcia
        self.animal_cb = QComboBox()
        form.addRow("Zwierzę:", self.animal_cb)

        # Wybór lekarza
        self.doctor_cb = QComboBox()
        self.doctors = DoctorService.list()
        for doc in self.doctors:
            self.doctor_cb.addItem(f"Dr {doc.first_name} {doc.last_name}", doc.id)
        form.addRow("Lekarz:", self.doctor_cb)

        # Data wizyty
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        form.addRow("Data:", self.date_edit)

        # Godzina wizyty
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        form.addRow("Godzina:", self.time_edit)

        # Pilne
        self.urgent_cb = QCheckBox()
        form.addRow("Pilne:", self.urgent_cb)

        # Powód wizyty
        self.reason_le = QLineEdit()
        form.addRow("Powód:", self.reason_le)

        # Przycisk zapisu
        self.schedule_btn = QPushButton("Zarezerwuj wizytę")
        self.schedule_btn.clicked.connect(self._on_schedule)

        layout.addLayout(form)
        layout.addWidget(self.schedule_btn)

        # Inicjalizacja listy zwierząt dla pierwszego klienta
        if self.clients:
            self._on_client_changed(0)

    def _on_client_changed(self, index):
        client_id = self.client_cb.itemData(index)
        all_animals = AnimalService.list()
        animals = [a for a in all_animals if getattr(a, 'owner_id', None) == client_id]
        self.animal_cb.clear()
        for animal in animals:
            self.animal_cb.addItem(animal.name, animal.id)

    def _on_schedule(self):
        owner_id = self.client_cb.currentData()
        animal_id = self.animal_cb.currentData()
        doctor_id = self.doctor_cb.currentData()
        qdate = self.date_edit.date()
        qtime = self.time_edit.time()
        visit_dt = datetime(
            qdate.year(), qdate.month(), qdate.day(),
            qtime.hour(), qtime.minute()
        ).isoformat()
        payload = {
            "owner_id": owner_id,
            "animal_id": animal_id,
            "doctor_id": doctor_id,
            "visit_datetime": visit_dt,
            "is_urgent": self.urgent_cb.isChecked(),
            "reason": self.reason_le.text(),
            "receptionist_id": self.receptionist_id,
        }
        try:
            AppointmentService.create(payload)
            QMessageBox.information(self, "Sukces", "Wizyta została zarezerwowana.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd rezerwacji", str(e))
