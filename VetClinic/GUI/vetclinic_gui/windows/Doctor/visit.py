from PyQt5.QtCore import QDateTime, pyqtSignal, Qt, QStringListModel
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QGroupBox, QDateTimeEdit, QComboBox, QTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QApplication, QSpinBox, QDoubleSpinBox,
    QScrollArea, QSplitter, QSizePolicy, QHeaderView,
    QLabel, QGridLayout, QCompleter
)
from PyQt5.QtGui import QFont
import sys

from vetclinic_gui.services.animals_service      import AnimalService
from vetclinic_gui.services.appointments_service import AppointmentService
from vetclinic_gui.services.clients_service      import ClientService


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

    def _groupbox_css(self) -> str:
        return """
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 12px;
                font-size: 18px;
                font-weight: bold;
                color: #111827;
                background-color: #ffffff;
            }
        """

    def _setup_ui(self):
        # --- Tytuł i wymiary okna ---
        self.setWindowTitle("Wizyty")
        self.resize(1200, 800)

        # --- 1) GŁÓWNY LAYOUT ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # --- 2) PASEK AKCJI ---
        top_bar = QHBoxLayout()
        self.search_le = QLineEdit()
        self.search_le.setPlaceholderText("🔍 Wyszukaj opiekuna...")
        self.search_le.setFixedHeight(30)
        self.search_le.setStyleSheet(
            "QLineEdit { border:1px solid #d1d5db; border-radius:15px; padding-left:10px; }"
        )
        self.search_le.textChanged.connect(self._filter_clients)

        self._owner_model     = QStringListModel(self)
        self._owner_completer = QCompleter(self._owner_model, self)
        self._owner_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._owner_completer.setFilterMode(Qt.MatchContains)
        self.search_le.setCompleter(self._owner_completer)
        self._owner_completer.activated.connect(self._on_owner_selected)
        self._completer_map = {}
        top_bar.addWidget(self.search_le)

        top_bar.addStretch()

        self.save_btn = QPushButton("Zapisz wizytę")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet(
            "QPushButton { padding:8px 16px; background-color:#38a2db; color:#fff; "
            "border:none; border-radius:15px; }"
            "QPushButton:hover { background-color:#2e3a50; }"
        )
        self.save_btn.clicked.connect(self._on_save_visit)
        top_bar.addWidget(self.save_btn)
        main_layout.addLayout(top_bar)

        # --- 3) INICJALIZACJA WIDGETÓW ---
        self.datetime_edit   = QDateTimeEdit(QDateTime.currentDateTime()); self.datetime_edit.setCalendarPopup(True)
        self.client_cb       = QComboBox(); self.client_cb.currentIndexChanged.connect(self._on_client_change)
        self.animal_cb       = QComboBox(); self.animal_cb.currentIndexChanged.connect(self._on_animal_change)
        self.status_cb       = QComboBox(); self.status_cb.addItems(["zaplanowana", "odwołana", "zakończona"])
        self.priority_cb     = QComboBox(); self.priority_cb.addItems(["normalna", "pilna", "nagła"])
        self.weight_visit_sb = QDoubleSpinBox(); self.weight_visit_sb.setRange(0.1, 500); self.weight_visit_sb.setSuffix(" kg"); self.weight_visit_sb.setSingleStep(0.1); self.weight_visit_sb.setDecimals(2)
        self.age_visit_sb    = QSpinBox(); self.age_visit_sb.setRange(0, 100)
        self.gender_visit_cb = QComboBox(); self.gender_visit_cb.addItems(["samiec", "samica"])
        self.reason_te       = QTextEdit(); self.reason_te.setFixedHeight(60)
        self.treatment_te    = QTextEdit(); self.treatment_te.setFixedHeight(100)

        self.species_le   = QLineEdit(); self.species_le.setReadOnly(True)
        self.breed_le     = QLineEdit(); self.breed_le.setReadOnly(True)
        self.gender_le    = QLineEdit(); self.gender_le.setReadOnly(True)
        self.birthdate_le = QLineEdit(); self.birthdate_le.setReadOnly(True)
        self.age_le       = QLineEdit(); self.age_le.setReadOnly(True)
        self.weight_le    = QLineEdit(); self.weight_le.setReadOnly(True)
        self.microchip_le = QLineEdit(); self.microchip_le.setReadOnly(True)
        self.animal_notes = QTextEdit(); self.animal_notes.setReadOnly(True); self.animal_notes.setFixedHeight(60)

        # --- 4) SEKCJA: Nowa wizyta ---
        form_box = QGroupBox()
        form_box.setStyleSheet(self._groupbox_css() + """
            /* cały tekst w sekcji */
            QLabel, QDateTimeEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
                font-family: "Segoe UI", sans-serif;
                font-size: 8pt;
            }
            /* pola formularza */
            QDateTimeEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
                background-color: #f9fafb;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 6px;             
            }
            /* odstęp hover/focus */
            QDateTimeEdit:hover, QComboBox:hover, QSpinBox:hover,
            QDoubleSpinBox:hover, QTextEdit:hover {
                border: 1px solid #38a2db;
            }
            QDateTimeEdit:focus, QComboBox:focus, QSpinBox:focus,
            QDoubleSpinBox:focus, QTextEdit:focus {
                border: 1px solid #256fb8;
            }
        """)   
        form_vbox = QVBoxLayout(form_box)
        form_vbox.setContentsMargins(8, 8, 8, 8)
        form_vbox.setSpacing(6)

        hdr_form = QHBoxLayout()
        lbl_form = QLabel("Nowa wizyta"); lbl_form.setFont(QFont('Arial', 12, QFont.Bold))
        hdr_form.addWidget(lbl_form); hdr_form.addStretch()
        form_vbox.addLayout(hdr_form)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFormAlignment(Qt.AlignLeft)
        form_layout.setHorizontalSpacing(16)
        form_layout.setVerticalSpacing(10)
        form_layout.addRow("Data i czas:", self.datetime_edit)
        form_layout.addRow("Właściciel:",  self.client_cb)
        form_layout.addRow("Zwierzę:",     self.animal_cb)
        form_layout.addRow("Status:",      self.status_cb)
        form_layout.addRow("Typ wizyty:",  self.priority_cb)
        form_layout.addRow("Waga (kg):",   self.weight_visit_sb)
        form_layout.addRow("Wiek:",        self.age_visit_sb)
        form_layout.addRow("Płeć:",        self.gender_visit_cb)
        form_layout.addRow("Powód wizyty:",self.reason_te)
        form_layout.addRow("Zastosowane leczenie:",self.treatment_te)
        form_vbox.addLayout(form_layout)

        # --- 5) SEKCJA: Dane zwierzęcia ---
        info_box = QGroupBox()
        info_box.setStyleSheet(self._groupbox_css())
        info_box.setContentsMargins(0, 0, 0, 0)

        info_box.setStyleSheet(self._groupbox_css() + """
            /* pola w sekcji Dane zwierzęcia */
            QLineEdit, QTextEdit {
                font-family: "Segoe UI", sans-serif;
                font-size: 8pt;
                background-color: #f9fafb;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 4px;
            }

            QLabel {
                color: #374151;
                font-size: 8pt;
            }
        """)

        info_vbox = QVBoxLayout(info_box)
        info_vbox.setContentsMargins(4, 4, 4, 4)
        info_vbox.setSpacing(4)
        info_box.setMaximumWidth(350)

        hdr_info = QHBoxLayout()
        hdr_info.setContentsMargins(0, 0, 0, 0)
        hdr_info.setSpacing(2)
        lbl_info = QLabel("Dane zwierzęcia")
        lbl_info.setFont(QFont('Arial', 12, QFont.Bold))
        hdr_info.addWidget(lbl_info)
        hdr_info.addStretch()
        info_vbox.addLayout(hdr_info)

        info_vbox.addSpacing(6)

        info_grid = QGridLayout()
        info_grid.setContentsMargins(0, 0, 0, 0)
        info_grid.setHorizontalSpacing(12)
        info_grid.setVerticalSpacing(8)

        fields = [
            ("Gatunek:", self.species_le),
            ("Rasa:",    self.breed_le),
            ("Płeć:",    self.gender_le),
            ("Data ur.:",self.birthdate_le),
            ("Wiek:",    self.age_le),
            ("Waga (kg):",self.weight_le),
            ("Mikroczip:",self.microchip_le),
            ("Uwagi:", self.animal_notes)
        ]

        for row, (text, widget) in enumerate(fields):
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            info_grid.addWidget(lbl, row, 0)

            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            info_grid.addWidget(widget, row, 1)
            info_grid.setRowStretch(row, 1)

        info_vbox.addLayout(info_grid, 1)

        # --- 6) GÓRNY SPLITTER: formularz + dane zwierzęcia ---
        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.addWidget(form_box)
        top_splitter.addWidget(info_box)
        top_splitter.setStretchFactor(0, 3)
        top_splitter.setStretchFactor(1, 2)
        main_layout.addWidget(top_splitter)

        # --- 7) SEKCJA: Poprzednie wizyty (dolny panel) ---
        prev_box = QGroupBox()
        prev_box.setStyleSheet(self._groupbox_css())
        prev_vbox = QVBoxLayout(prev_box)
        prev_vbox.setContentsMargins(8, 8, 8, 8)
        prev_vbox.setSpacing(6)

        hdr_prev = QHBoxLayout()
        lbl_prev = QLabel("Poprzednie wizyty"); lbl_prev.setFont(QFont('Arial', 12, QFont.Bold))
        hdr_prev.addWidget(lbl_prev); hdr_prev.addStretch()
        prev_vbox.addLayout(hdr_prev)

        self.prev_table = QTableWidget(0, 7)
        self.prev_table.setHorizontalHeaderLabels(
            ["ID", "Data i czas", "Zwierzę", "Właściciel", "Waga (kg)", "Powód", "Leczenie"]
        )
        self.prev_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.prev_table.setSelectionMode(QTableWidget.NoSelection)
        self.prev_table.setFocusPolicy(Qt.NoFocus)
        self.prev_table.verticalHeader().setVisible(False)
        self.prev_table.setAlternatingRowColors(True)

        # prosta stylizacja
        self.prev_table.setStyleSheet("""
            QHeaderView::section {
                background-color: #f3f4f6;
                padding: 6px;
                border: none;
                font-weight: 600;
                color: #111827;
                border-bottom: 2px solid #e5e7eb;
            }
            QTableWidget {
                background-color: #ffffff;
                gridline-color: #e5e7eb;
            }
            QTableWidget::item {
                padding: 4px 8px;
            }
        """)

        hdr = self.prev_table.horizontalHeader()
        # Kolumny 0–4: ResizeToContents
        for col in range(5):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        # Kolumny 5–6: Stretch
        hdr.setSectionResizeMode(5, QHeaderView.Stretch)
        hdr.setSectionResizeMode(6, QHeaderView.Stretch)

        self.prev_table.cellDoubleClicked.connect(self._on_edit_visit)
        prev_vbox.addWidget(self.prev_table)

        prev_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(prev_box)

    def _load_data(self):
        self.clients = ClientService.list()
        self._populate_clients(self.clients)
        self._update_owner_completer()

        self.animals  = AnimalService.list()
        self._populate_animals(self.animals)

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

    def _update_owner_completer(self):
        suggestions = []
        self._completer_map.clear()
        for c in self.clients:
            full = f"{c.first_name} {c.last_name}"
            suggestions.append(full)
            self._completer_map[full] = c.id
        for a in self.animals:
            suggestions.append(a.name)
            self._completer_map[a.name] = a.owner_id
        self._owner_model.setStringList(suggestions)

    def _on_owner_selected(self, text: str):
        owner_id = self._completer_map.get(text)
        if owner_id is None:
            return
        idx = self.client_cb.findData(owner_id)
        if idx == -1:
            return
        self.client_cb.blockSignals(True)
        self.client_cb.setCurrentIndex(idx)
        self.client_cb.blockSignals(False)
        self._on_client_change(idx)

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
        aid = self.animal_cb.currentData()
        animal = next((a for a in self.animals if a.id == aid), None)
        if not animal:
            return

        self.species_le.setText(animal.species or "")
        self.breed_le.setText(animal.breed or "")
        self.gender_le.setText(animal.gender or "")

        bd = animal.birth_date
        bd_str = bd.isoformat() if hasattr(bd, "isoformat") else str(bd or "")
        self.birthdate_le.setText(bd_str)

        self.age_le.setText(str(animal.age or ""))
        if animal.weight is not None:
            self.weight_le.setText(f"{animal.weight:.1f}")
        else:
            self.weight_le.clear()

        self.microchip_le.setText(animal.microchip_number or "")
        self.animal_notes.setPlainText(animal.notes or "")

        self.age_visit_sb.setValue(animal.age or 0)
        self.weight_visit_sb.setValue(animal.weight or 0.0)

        gi = self.gender_visit_cb.findText(animal.gender or "")
        if gi >= 0:
            self.gender_visit_cb.setCurrentIndex(gi)

        oi = self.client_cb.findData(animal.owner_id)
        if oi != -1:
            self.client_cb.blockSignals(True)
            self.client_cb.setCurrentIndex(oi)
            self.client_cb.blockSignals(False)

        self._load_previous_visits()

    def _load_previous_visits(self):
        # pobierz wszystkie wizyty z serwisu i odfiltruj po zwierzęciu i lekarzu
        all_v = AppointmentService.list()
        aid   = self.animal_cb.currentData()
        visits = [v for v in all_v
                  if v.animal_id == aid and v.doctor_id == self.doctor_id]

        # wyczyść tabelę
        self.prev_table.setRowCount(0)

        for v in visits:
            r = self.prev_table.rowCount()
            self.prev_table.insertRow(r)

            # znajdź zwierzę po id
            animal = next((a for a in self.animals if a.id == v.animal_id), None)
            owner  = next((c for c in self.clients if c.id == v.owner_id), None)

            # sformatuj pola
            date_str      = v.visit_datetime  # zakładam, że to string ISO
            animal_str    = animal.name if animal else ""
            owner_str     = f"{owner.first_name} {owner.last_name}" if owner else ""
            w = getattr(v, "weight", None)
            weight_str    = f"{w:.1f}" if isinstance(w, (int, float)) else ""
            reason_str    = v.reason or ""
            treatment_str = getattr(v, "treatment", "") or ""

            values = [
                v.id,
                date_str,
                animal_str,
                owner_str,
                weight_str,
                reason_str,
                treatment_str
            ]

            for c, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                # kolumny ID i Waga wyrównaj do prawej
                if c in (0, 4):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignLeft  | Qt.AlignVCenter)
                self.prev_table.setItem(r, c, item)

    def _on_save_visit(self):
        # 1) zaktualizuj dane zwierzęcia
        aid = self.animal_cb.currentData()
        AnimalService.update(aid, {
            "weight": self.weight_visit_sb.value(),
            "age":    self.age_visit_sb.value(),
            "gender": self.gender_visit_cb.currentText()
        })

        # 2) zbierz wartości z UI
        doctor_id = self.doctor_id
        if doctor_id is None:
            QMessageBox.critical(self, "Błąd", "Nieznany identyfikator lekarza!")
            return

        payload = {
            "doctor_id":      doctor_id,
            "animal_id":      aid,
            "owner_id":       self.client_cb.currentData(),
            "visit_datetime": self.datetime_edit.dateTime().toString(Qt.ISODate),
            "reason":         self.reason_te.toPlainText(),
            "treatment":      self.treatment_te.toPlainText(),
            "priority":       self.priority_cb.currentText(),
            "weight":         self.weight_visit_sb.value()
        }

        # 3) utwórz lub zaktualizuj
        try:
            if hasattr(self, "editing_id"):
                AppointmentService.update(self.editing_id, payload)
                del self.editing_id
            else:
                AppointmentService.create(payload)
        except Exception as e:
            QMessageBox.critical(self, "Błąd zapisu wizyty", str(e))
            return

        # 4) odśwież i powiadom
        QMessageBox.information(self, "Sukces", "Wizyta zapisana.")
        self._load_previous_visits()

    def _on_edit_visit(self, row: int, col: int):
        # 1) Pobierz ID wizyty z tabeli
        vid = int(self.prev_table.item(row, 0).text())
        # 2) Pobierz obiekt z serwisu
        visit = AppointmentService.get(vid)
        self.editing_id = vid

        # 3) Data i czas
        # visit.visit_datetime jest datetime.datetime -> zamieniamy na QDateTime
        dt_str = visit.visit_datetime.isoformat()
        self.datetime_edit.setDateTime(QDateTime.fromString(dt_str, Qt.ISODate))

        # 4) Comboboxy
        # (zakładam, że nadal masz klienta i zwierzę)
        self.client_cb.setCurrentIndex(self.client_cb.findData(visit.owner_id))
        self.animal_cb.setCurrentIndex(self.animal_cb.findData(visit.animal_id))

        # 5) Priorytet
        self.priority_cb.setCurrentText(visit.priority or "")

        # 6) Pola tekstowe
        self.reason_te.setPlainText(visit.reason or "")
        # zamiast notes_te ustawiamy treatment_te
        self.treatment_te.setPlainText(getattr(visit, "treatment", "") or "")

        # 7) SpinBoxy
        self.weight_visit_sb.setValue(visit.weight or 0.0)
        # jeśli trzymasz wiek w wizytach:
        if hasattr(visit, "age"):
            self.age_visit_sb.setValue(visit.age or 0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = VisitsWindow(doctor_id=1)
    w.show()
    sys.exit(app.exec_())
