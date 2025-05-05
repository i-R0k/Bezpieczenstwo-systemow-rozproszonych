from PyQt5.QtCore import QDateTime, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QGroupBox, QDateTimeEdit, QComboBox, QTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QApplication
)
from vetclinic_gui.services.animals_service import AnimalService
from vetclinic_gui.services.appointments_service import AppointmentService
from vetclinic_gui.services.clients_service import UserService
import sys

class VisitsWindow(QWidget):
    """
    Ekran zarządzania wizytami dla danego lekarza.
    """
    navigate = pyqtSignal(str)

    def __init__(self, doctor_id: int):
        super().__init__()
        self.doctor_id = doctor_id
        self.clients = []  # lista załadowanych klientów
        self._setup_ui()
        self._load_animals()
        self._load_clients()
        self._load_previous_visits()

    def _setup_ui(self):
       self.setWindowTitle("Wizyty")
       # główny układ pionowy
       layout = QVBoxLayout(self)
       layout.setContentsMargins(15, 15, 15, 15)
       layout.setSpacing(10)

       # --- Wyszukaj opiekuna ---
       self.search_le = QLineEdit()
       self.search_le.setPlaceholderText("🔍 Wyszukaj opiekuna...")
       self.search_le.setStyleSheet(
           "QLineEdit { border:1px solid #ccc; border-radius:20px; padding:8px 12px; background:#fff; }"
           "QLineEdit:focus { border:1px solid #38a2db; }"
       )
       self.search_le.textChanged.connect(self._filter_owners)
       layout.addWidget(self.search_le)

       # --- Pasek akcji (przycisk Zapisz) ---
       bar = QHBoxLayout()
       bar.addStretch()
       self.save_btn = QPushButton("Zapisz wizytę")
       self.save_btn.setCursor(Qt.PointingHandCursor)
       self.save_btn.setStyleSheet(
           "QPushButton { background-color:#38a2db; color:#fff; padding:8px 16px; border:none; border-radius:4px; }"
           "QPushButton:hover { background-color:#2f8acb; }"
       )
       self.save_btn.clicked.connect(self._on_save_visit)
       bar.addWidget(self.save_btn)
       layout.addLayout(bar)

       # --- Formularz wizyty (Appointment) ---
       form_box = QGroupBox("Nowa wizyta")
       form_box.setStyleSheet(
           "QGroupBox { background:#fff; border:1px solid #e0e0e0; border-radius:8px; padding:12px; }"
           "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding:0 5px; font-weight:bold; }"
       )
       form_layout = QFormLayout(form_box)
       self.datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
       self.datetime_edit.setCalendarPopup(True)
       self.animal_cb = QComboBox()
       self.client_cb = QComboBox()
       self.status_cb = QComboBox()
       self.status_cb.addItems(["zaplanowana", "odwołana", "zakończona"])
       self.reason_te = QTextEdit()
       self.reason_te.setFixedHeight(60)
       self.notes_te = QTextEdit()
       self.notes_te.setFixedHeight(80)

       form_layout.addRow("Data i czas:",      self.datetime_edit)
       form_layout.addRow("Zwierzę:",           self.animal_cb)
       form_layout.addRow("Właściciel:",        self.client_cb)
       form_layout.addRow("Status:",            self.status_cb)
       form_layout.addRow("Powód wizyty:",      self.reason_te)
       form_layout.addRow("Uwagi wizyty:",      self.notes_te)
       layout.addWidget(form_box)

       # --- Dane zwierzęcia (Animal) ---
       info_box = QGroupBox("Dane zwierzęcia")
       info_box.setStyleSheet(form_box.styleSheet())
       info_layout = QFormLayout(info_box)
       self.species_le      = QLineEdit()
       self.breed_le        = QLineEdit()
       self.gender_le       = QLineEdit()
       self.birthdate_le    = QLineEdit()
       self.age_le          = QLineEdit()
       self.weight_le       = QLineEdit()
       self.microchip_le    = QLineEdit()
       self.animal_notes_te = QTextEdit()
       self.animal_notes_te.setFixedHeight(60)

       info_layout.addRow("Gatunek:",           self.species_le)
       info_layout.addRow("Rasa:",              self.breed_le)
       info_layout.addRow("Płeć:",              self.gender_le)
       info_layout.addRow("Data ur.:",          self.birthdate_le)
       info_layout.addRow("Wiek:",              self.age_le)
       info_layout.addRow("Waga (kg):",         self.weight_le)
       info_layout.addRow("Mikroczip:",         self.microchip_le)
       info_layout.addRow("Uwagi zwierzęcia:",  self.animal_notes_te)
       layout.addWidget(info_box)

       # --- Poprzednie wizyty ---
       prev_box = QGroupBox("Poprzednie wizyty")
       prev_box.setStyleSheet(form_box.styleSheet())
       prev_layout = QVBoxLayout(prev_box)
       self.prev_table = QTableWidget(0, 6)
       self.prev_table.setHorizontalHeaderLabels([
           "ID", "Data i czas", "Zwierzę", "Właściciel", "Status", "Powód"
       ])
       self.prev_table.cellDoubleClicked.connect(self._on_edit_visit)
       prev_layout.addWidget(self.prev_table)
       layout.addWidget(prev_box)

    def _load_animals(self):
        # 1) pobieramy wszystkie obiekty Animal i zapisujemy je w self.animals
        self.animals = AnimalService.list()
        # 2) czyścimy combobox
        self.animal_cb.clear()
        # 3) wypełniamy go na podstawie atrybutów obiektów
        for animal in self.animals:
            self.animal_cb.addItem(animal.name, animal.id)

        # 4) jeśli mamy przynajmniej jedno zwierzę, ustawiamy je jako wybrane
        if self.animals:
            self.animal_cb.setCurrentIndex(0)
            # i od razu aktualizujemy pola formularza
            self._on_animal_change(0)
    
    def _load_clients(self):
        self.clients = UserService.list()
        self.client_cb.clear()
        for client in self.clients:
            name = f"{client.first_name} {client.last_name}"
            self.client_cb.addItem(name, client.id)
    
    def _refresh_client_cb(self, clients):
        self.client_cb.clear()
        for c in clients:
            full = f"{c.get('first_name','')} {c.get('last_name','')}"
            self.client_cb.addItem(full, c['id'])

    def _filter_owners(self, text: str):
        keyword = text.lower().strip()
        if not keyword:
            filtered = self.clients
        else:
            filtered = [c for c in self.clients if keyword in f"{c.get('first_name','')} {c.get('last_name','')}".lower()]
        self._refresh_client_cb(filtered)

    def _load_previous_visits(self):
        # pobieramy wszystkie wizyty z serwisu
        all_visits = AppointmentService.list()
        # ID aktualnie wybranego zwierzęcia i zalogowanego lekarza
        aid = self.animal_cb.currentData()
        did = self.doctor_id

        # czyścimy tabelę
        self.prev_table.setRowCount(0)

        # filtrujemy obiekty Appointment zamiast słowników
        for visit in all_visits:
            if visit.animal_id == aid and visit.doctor_id == did:
                row = self.prev_table.rowCount()
                self.prev_table.insertRow(row)

                # przygotowujemy wartości do wstawienia
                values = [
                    visit.id,
                    # formatujemy datę i czas
                    visit.visit_datetime.strftime("%Y-%m-%d %H:%M"),
                    # relacja do Animal
                    visit.animal.name,
                    # relacja do Client/Owner
                    f"{visit.owner.first_name} {visit.owner.last_name}",
                    visit.status,
                    visit.reason or ""
                ]

                # wypełniamy komórki tabeli
                for col, val in enumerate(values):
                    self.prev_table.setItem(row, col, QTableWidgetItem(str(val)))

    def _on_save_visit(self):
        payload = {
            'doctor_id': self.doctor_id,
            'animal_id': self.animal_cb.currentData(),
            'owner_id': self.client_cb.currentData(),
            'visit_datetime': self.datetime_edit.dateTime().toString(Qt.ISODate),
            'status': self.status_cb.currentText(),
            'reason': self.reason_te.toPlainText(),
            'notes': self.notes_te.toPlainText()
        }
        if hasattr(self, 'editing_id'):
            AppointmentService.update(self.editing_id, payload)
            del self.editing_id
        else:
            AppointmentService.create(payload)
        QMessageBox.information(self, "Sukces", "Wizyta zapisana.")
        self._load_previous_visits()

    def _on_edit_visit(self, row, col):
        vid = int(self.prev_table.item(row,0).text())
        visit = AppointmentService.get(vid)
        self.editing_id = vid
        self.datetime_edit.setDateTime(QDateTime.fromString(visit['visit_datetime'], Qt.ISODate))
        self.animal_cb.setCurrentIndex(self.animal_cb.findData(visit['animal_id']))
        self.client_cb.setCurrentIndex(self.client_cb.findData(visit['owner_id']))
        self.status_cb.setCurrentText(visit['status'])
        self.reason_te.setPlainText(visit.get('reason',''))
        self.notes_te.setPlainText(visit.get('notes',''))

    def _on_animal_change(self, index: int):
        # pobieramy aktualne ID zwierzęcia z comboboxa
        animal_id = self.animal_cb.currentData()
        # szukamy instancji Animal w liście self.animals
        animal = next((a for a in self.animals if a.id == animal_id), None)
        if not animal:
            return

        # wczytanie pól Animal
        self.species_le.setText(animal.species or "")
        self.breed_le.setText(animal.breed or "")
        self.gender_le.setText(animal.gender or "")
        self.birthdate_le.setText(animal.birth_date.isoformat() if animal.birth_date else "")
        self.age_le.setText(str(animal.age) if animal.age is not None else "")
        self.weight_le.setText(str(animal.weight) if animal.weight is not None else "")
        self.microchip_le.setText(animal.microchip_number or "")
        self.animal_notes_te.setPlainText(animal.notes or "")

        # ustawienie comboboxa właściciela – korzystamy z self.client_cb
        # i listy self.clients wypełnionej w _load_users
        owner_idx = self.client_cb.findData(animal.owner_id)
        if owner_idx != -1:
            self.client_cb.setCurrentIndex(owner_idx)

        # odświeżamy poprzednie wizyty
        self._load_previous_visits()
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = VisitsWindow(doctor_id=1)
    w.show()
    sys.exit(app.exec_())
