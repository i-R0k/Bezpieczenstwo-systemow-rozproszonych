from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QLabel,
    QPushButton, QMessageBox, QTabWidget, QTableWidget, QTableWidgetItem
)
from datetime import datetime, date

from vetclinic_gui.services.clients_service import ClientService
from vetclinic_gui.services.appointments_service import AppointmentService

class ReceptionistDashboardPage(QWidget):
    """
    Dashboard recepcjonisty - przegląd wizyt: przeszłe, dzisiejsze i przyszłe.
    """
    def __init__(self, receptionist_id=None):
        super().__init__()
        self.receptionist_id = receptionist_id
        self._setup_ui()
        self._load_visits()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Przegląd wizyt")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        # Tabele dla trzech kategorii wizyt
        self.past_table = QTableWidget(0, 4)
        self.today_table = QTableWidget(0, 4)
        self.upcoming_table = QTableWidget(0, 4)
        for tbl in (self.past_table, self.today_table, self.upcoming_table):
            tbl.setHorizontalHeaderLabels(["Data", "Godzina", "Gabinet", "Lekarz"])
        self.tabs.addTab(self.past_table, "Przeszłe")
        self.tabs.addTab(self.today_table, "Dzisiejsze")
        self.tabs.addTab(self.upcoming_table, "Przyszłe")
        layout.addWidget(self.tabs)

    def _load_visits(self):
        all_visits = AppointmentService.list()
        now = datetime.now()
        today_date = date.today()
        # Czyścimy tabele
        for tbl in (self.past_table, self.today_table, self.upcoming_table):
            tbl.setRowCount(0)

        for v in all_visits:
            try:
                dt = datetime.fromisoformat(v.visit_datetime)
            except Exception:
                continue
            # Wybór tabeli według daty wizyty
            if dt.date() < today_date:
                tbl = self.past_table
            elif dt.date() == today_date:
                tbl = self.today_table
            else:
                tbl = self.upcoming_table

            row = tbl.rowCount()
            tbl.insertRow(row)
            date_str = dt.date().isoformat()
            time_str = dt.strftime("%H:%M")

            # Pobranie nazwy gabinetu
            room = next((r for r in AppointmentService._rooms if getattr(r, 'id', None) == v.room_id), None)
            room_name = getattr(room, 'name', '') if room else ''
            # Pobranie danych lekarza
            doctor = next((d for d in AppointmentService._doctors if getattr(d, 'id', None) == v.doctor_id), None)
            doctor_name = f"{doctor.first_name} {doctor.last_name}" if doctor else ''

            values = [date_str, time_str, room_name, doctor_name]
            for col, val in enumerate(values):
                tbl.setItem(row, col, QTableWidgetItem(val))
