from PyQt5.QtCore import QDateTime, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QGroupBox, QDateTimeEdit, QComboBox, QTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QApplication
)
import sys

from vetclinic_gui.services.animals_service      import AnimalService
from vetclinic_gui.services.appointments_service import AppointmentService
from vetclinic_gui.services.clients_service      import UserService

class VisitsWindow(QWidget):
    navigate = pyqtSignal(str)

    def __init__(self, doctor_id: int):
        super().__init__()
        self.doctor_id = doctor_id

        # miejsce na wszystkie rekordy pobrane z API:
        self.clients = []
        self.animals = []

        self._setup_ui()
        self._load_data()   # teraz wczytamy i zintegrujemy wszystko

    def _setup_ui(self):
        self.setWindowTitle("Wizyty")
        self.resize(1200, 800)

        main = QVBoxLayout(self)
        main.setContentsMargins(15,15,15,15)
        main.setSpacing(10)

        # --- Search bar (filter klientów) ---
        self.search_le = QLineEdit()
        self.search_le.setPlaceholderText("🔍 Wyszukaj opiekuna...")
        self.search_le.setStyleSheet(
            "QLineEdit{border:1px solid #ccc; border-radius:20px; padding:8px 12px;}"
            "QLineEdit:focus{border-color:#38a2db;}"
        )
        self.search_le.textChanged.connect(self._filter_clients)
        main.addWidget(self.search_le)

        # --- Action bar ---
        hb = QHBoxLayout(); hb.addStretch()
        self.save_btn = QPushButton("Zapisz wizytę")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet(
            "QPushButton{background:#38a2db;color:#fff;padding:8px 16px;border-radius:4px;}"
            "QPushButton:hover{background:#2f8acb;}"
        )
        self.save_btn.clicked.connect(self._on_save_visit)
        hb.addWidget(self.save_btn)
        main.addLayout(hb)

        # --- Formularz wizyty ---
        self.datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)
        self.animal_cb   = QComboBox()
        self.client_cb   = QComboBox()
        self.status_cb   = QComboBox(); self.status_cb.addItems(["zaplanowana","odwołana","zakończona"])
        self.reason_te   = QTextEdit(); self.reason_te.setFixedHeight(60)
        self.notes_te    = QTextEdit(); self.notes_te.setFixedHeight(80)

        # kiedy się zmieni zwierzę lub klient:
        self.animal_cb.currentIndexChanged.connect(self._on_animal_change)
        self.client_cb.currentIndexChanged.connect(self._on_client_change)

        form_box = QGroupBox("Nowa wizyta")
        form_box.setStyleSheet("QGroupBox{background:#fff;border:1px solid #e0e0e0;border-radius:8px;}") 
        frm = QFormLayout(form_box)
        frm.addRow("Data i czas:",   self.datetime_edit)
        frm.addRow("Zwierzę:",       self.animal_cb)
        frm.addRow("Właściciel:",    self.client_cb)
        frm.addRow("Status:",        self.status_cb)
        frm.addRow("Powód wizyty:",  self.reason_te)
        frm.addRow("Uwagi wizyty:",  self.notes_te)
        main.addWidget(form_box)

        # --- Dane zwierzęcia ---
        self.species_le    = QLineEdit();  self.species_le.setReadOnly(True)
        self.breed_le      = QLineEdit();  self.breed_le.setReadOnly(True)
        self.gender_le     = QLineEdit();  self.gender_le.setReadOnly(True)
        self.birthdate_le  = QLineEdit();  self.birthdate_le.setReadOnly(True)
        self.age_le        = QLineEdit();  self.age_le.setReadOnly(True)
        self.weight_le     = QLineEdit();  self.weight_le.setReadOnly(True)
        self.microchip_le  = QLineEdit();  self.microchip_le.setReadOnly(True)
        self.animal_notes  = QTextEdit();  self.animal_notes.setReadOnly(True); self.animal_notes.setFixedHeight(60)

        info_box = QGroupBox("Dane zwierzęcia")
        info_box.setStyleSheet(form_box.styleSheet())
        inf = QFormLayout(info_box)
        inf.addRow("Gatunek:",        self.species_le)
        inf.addRow("Rasa:",           self.breed_le)
        inf.addRow("Płeć:",           self.gender_le)
        inf.addRow("Data ur.:",       self.birthdate_le)
        inf.addRow("Wiek:",           self.age_le)
        inf.addRow("Waga (kg):",      self.weight_le)
        inf.addRow("Mikroczip:",      self.microchip_le)
        inf.addRow("Uwagi zwierzęcia:", self.animal_notes)
        main.addWidget(info_box)

        # --- Poprzednie wizyty ---
        self.prev_table = QTableWidget(0,6)
        self.prev_table.setHorizontalHeaderLabels([
            "ID","Data i czas","Zwierzę","Właściciel","Status","Powód"
        ])
        self.prev_table.cellDoubleClicked.connect(self._on_edit_visit)
        prev_box = QGroupBox("Poprzednie wizyty")
        prev_box.setStyleSheet(form_box.styleSheet())
        vb = QVBoxLayout(prev_box)
        vb.addWidget(self.prev_table)
        main.addWidget(prev_box)

    def _load_data(self):
        # pobierz z API i zapamiętaj
        self.clients = UserService.list()
        self._populate_clients(self.clients)

        self.animals  = AnimalService.list()
        # na start wyświetlam wszystkich, ale _on_client_change zaindeksuje
        self._populate_animals(self.animals)

        # wywołaj raz, aby spiąć pola
        if self.client_cb.count(): 
            self._on_client_change(0)

    def _populate_clients(self, clients_list):
        self.client_cb.blockSignals(True)
        self.client_cb.clear()
        for c in clients_list:
            label = f"{c.first_name} {c.last_name}"
            self.client_cb.addItem(label, c.id)
        self.client_cb.blockSignals(False)

    def _populate_animals(self, animals_list):
        self.animal_cb.blockSignals(True)
        self.animal_cb.clear()
        for a in animals_list:
            self.animal_cb.addItem(a.name, a.id)
        self.animal_cb.blockSignals(False)

    def _filter_clients(self, text: str):
        txt = text.lower()
        filtered = [c for c in self.clients
                    if txt in f"{c.first_name} {c.last_name}".lower()]
        self._populate_clients(filtered)
        # od razu odświeżamy zwierzęta dla nowego zaznaczenia
        if self.client_cb.count():
            self._on_client_change(0)

    def _on_client_change(self, index: int):
        owner_id = self.client_cb.currentData()
        # pokażemy tylko zwierzęta tego właściciela
        own_animals = [a for a in self.animals if a.owner_id == owner_id]
        self._populate_animals(own_animals)
        # i od razu zaktualizuj szczegóły dla pierwszego
        if own_animals:
            self._on_animal_change(0)
        else:
            # jeżeli brak zwierząt, wyczyść pola
            for w in [self.species_le, self.breed_le, self.gender_le,
                      self.birthdate_le, self.age_le, self.weight_le,
                      self.microchip_le, self.animal_notes]:
                w.clear()
            self.prev_table.setRowCount(0)

    def _on_animal_change(self, index: int):
        animal_id = self.animal_cb.currentData()
        animal = next((a for a in self.animals if a.id == animal_id), None)
        if not animal:
            return

        # gatunek, rasa, płeć
        self.species_le.setText(animal.species or "")
        self.breed_le.setText(animal.breed or "")
        self.gender_le.setText(animal.gender or "")

        # data urodzenia jako string
        if animal.birth_date:
            # jeśli birth_date jest datetime.date
            bd_str = (
                animal.birth_date.isoformat()
                if hasattr(animal.birth_date, "isoformat")
                else str(animal.birth_date)
            )
        else:
            bd_str = ""
        self.birthdate_le.setText(bd_str)

        # wiek i waga
        self.age_le.setText(str(animal.age or ""))
        self.weight_le.setText(str(animal.weight or ""))

        # mikroczip i notatki
        self.microchip_le.setText(animal.microchip_number or "")
        self.animal_notes.setPlainText(animal.notes or "")

        # upewnij się, że combobox właściciela wskazuje prawidłowe ID
        owner_idx = self.client_cb.findData(animal.owner_id)
        if owner_idx != -1:
            self.client_cb.blockSignals(True)
            self.client_cb.setCurrentIndex(owner_idx)
            self.client_cb.blockSignals(False)

        # odśwież poprzednie wizyty
        self._load_previous_visits()


    def _load_previous_visits(self):
        all_v = AppointmentService.list()
        aid = self.animal_cb.currentData()
        visits = [v for v in all_v
                  if v.animal_id == aid and v.doctor_id == self.doctor_id]

        self.prev_table.setRowCount(0)
        for v in visits:
            r = self.prev_table.rowCount(); self.prev_table.insertRow(r)
            for c, key in enumerate(
                ["id","visit_datetime","animal_name","owner_name","status","reason"]
            ):
                self.prev_table.setItem(r, c, QTableWidgetItem(str(getattr(v, key, ""))))  

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = VisitsWindow(doctor_id=1)
    w.show()
    sys.exit(app.exec_())
