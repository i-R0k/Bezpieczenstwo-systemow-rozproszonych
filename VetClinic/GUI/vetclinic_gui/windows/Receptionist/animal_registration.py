from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QLabel,
    QPushButton, QMessageBox, QFrame, QSizePolicy,
    QDateEdit, QDoubleSpinBox, QTextEdit, QCompleter, QComboBox
)
from PyQt5.QtCore import Qt, QDate, QStringListModel
from datetime import date

from vetclinic_gui.services.clients_service import ClientService
from vetclinic_gui.services.animals_service import AnimalService

class AnimalRegistrationPage(QWidget):
    def __init__(self, receptionist_id=None):
        super().__init__()
        self.receptionist_id = receptionist_id
        self._selected_owner_id = None
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background-color: #F3F4F6;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addStretch()

        card = QFrame()
        card.setMaximumWidth(600)
        card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid rgba(0,0,0,0.07);
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(16)

        title = QLabel("Rejestracja nowego zwierzęcia")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1F2937;
        """)
        card_layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setFormAlignment(Qt.AlignCenter)
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(12)

        self.name_le    = QLineEdit();    self.name_le.setPlaceholderText("Np. Burek")
        self.species_le = QLineEdit();    self.species_le.setPlaceholderText("Np. pies, kot")
        self.breed_le   = QLineEdit();    self.breed_le.setPlaceholderText("Np. owczarek niem.")

        self.gender_cb  = QComboBox()
        self.gender_cb.addItem("– wybierz –", None)
        self.gender_cb.addItem("Samiec",      "male")
        self.gender_cb.addItem("Samica",      "female")
        self.gender_cb.addItem("Nieznana",    "unknown")

        self.dob_de     = QDateEdit(calendarPopup=True)
        self.dob_de.setDisplayFormat("yyyy-MM-dd")
        self.dob_de.setDate(QDate.currentDate())
        self.weight_ds  = QDoubleSpinBox()
        self.weight_ds.setRange(0.0, 500.0)
        self.weight_ds.setDecimals(2)
        self.weight_ds.setSuffix(" kg")
        self.chip_le    = QLineEdit();    self.chip_le.setPlaceholderText("Numer mikroczipa")
        self.notes_te   = QTextEdit();    self.notes_te.setPlaceholderText("Dodatkowe uwagi")
        self.notes_te.setFixedHeight(80)

        self.owner_le = QLineEdit()
        self.owner_le.setPlaceholderText("Wyszukaj właściciela (imię, nazwisko, adres)")
        owners = ClientService.list() or []
        self._owner_map = {}
        suggestions = []
        for c in owners:
            txt = f"{c.first_name} {c.last_name}, {c.address}"
            suggestions.append(txt)
            self._owner_map[txt] = c.id
        model = QStringListModel(suggestions)
        completer = QCompleter(model, self.owner_le)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        completer.activated[str].connect(self._on_owner_chosen)
        self.owner_le.setCompleter(completer)

        self.owner_le.textChanged.connect(lambda prefix: (completer.setCompletionPrefix(prefix), completer.complete()))
        self._owner_completer = completer

        widget_style = """
            QLineEdit, QDateEdit, QComboBox, QDoubleSpinBox {
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                color: #374151;
            }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #2563EB;
            }
        """
        for w in (
            self.name_le, self.species_le, self.breed_le,
            self.gender_cb, self.dob_de, self.weight_ds,
            self.chip_le, self.owner_le
        ):
            w.setStyleSheet(widget_style)
        self.notes_te.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                color: #374151;
            }
            QTextEdit:focus { border: 1px solid #2563EB; }
        """)

        form.addRow("Imię zwierzęcia:", self.name_le)
        form.addRow("Gatunek:",         self.species_le)
        form.addRow("Rasa:",            self.breed_le)
        form.addRow("Płeć:",            self.gender_cb)
        form.addRow("Data ur.:",        self.dob_de)
        form.addRow("Waga:",            self.weight_ds)
        form.addRow("Mikroczip #:",      self.chip_le)
        form.addRow("Notatki:",          self.notes_te)
        form.addRow("Właściciel:",       self.owner_le)

        card_layout.addLayout(form)

        self.register_btn = QPushButton("Zarejestruj zwierzę")
        self.register_btn.setFixedHeight(40)
        self.register_btn.setCursor(Qt.PointingHandCursor)
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 0 24px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:pressed { background-color: #1E40AF; }
        """)
        self.register_btn.clicked.connect(self._on_register)

        btn_ctr = QFrame()
        btn_ctr.setLayout(QVBoxLayout())
        btn_ctr.layout().setContentsMargins(0, 0, 0, 0)
        btn_ctr.layout().setAlignment(Qt.AlignCenter)
        btn_ctr.layout().addWidget(self.register_btn)
        card_layout.addWidget(btn_ctr)

        main_layout.addWidget(card, alignment=Qt.AlignHCenter)
        main_layout.addStretch()


    def _on_owner_chosen(self, text: str):
        """Zapisujemy wybranego właściciela."""
        self._selected_owner_id = self._owner_map.get(text)

    def _on_register(self):
        missing = []
        if not self.name_le.text().strip():    missing.append("Imię zwierzęcia")
        if not self.species_le.text().strip(): missing.append("Gatunek")
        if not self._selected_owner_id:        missing.append("Właściciel")
        if missing:
            QMessageBox.warning(
                self, "Brak danych",
                "Uzupełnij pola:\n" + "\n".join(missing)
            )
            return

        dob = self.dob_de.date().toPyDate()
        today = date.today()
        years = today.year - dob.year
        months = today.month - dob.month
        if today.day < dob.day:
            months -= 1
        total_months = years * 12 + months
        age_decimal = round(total_months / 12, 1)

        payload = {
            "name":             self.name_le.text().strip(),
            "species":          self.species_le.text().strip(),
            "breed":            self.breed_le.text().strip() or None,
            "gender":           self.gender_le.text().strip() or None,
            "birth_date":       dob.isoformat(),
            "age":              age_decimal,
            "weight":           self.weight_ds.value() or None,
            "microchip_number": self.chip_le.text().strip() or None,
            "notes":            self.notes_te.toPlainText().strip() or None,
            "owner_id":         self._selected_owner_id,
        }

        try:
            AnimalService.create(payload)
            QMessageBox.information(self, "Sukces", "Zwierzę zostało zarejestrowane.")
            for w in (
                self.name_le, self.species_le, self.breed_le,
                self.gender_le, self.dob_de, self.weight_ds,
                self.chip_le, self.notes_te, self.owner_le
            ):
                if isinstance(w, (QLineEdit, QTextEdit)):
                    w.clear()
                elif isinstance(w, QDateEdit):
                    w.setDate(QDate.currentDate())
                elif isinstance(w, QDoubleSpinBox):
                    w.setValue(0.0)
            self._selected_owner_id = None
        except Exception as e:
            QMessageBox.critical(self, "Błąd rejestracji", str(e))
