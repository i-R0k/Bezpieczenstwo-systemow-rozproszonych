from PyQt5.QtCore import QDateTime, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QGroupBox, QDateTimeEdit, QComboBox, QTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QApplication
)
import sys

class VisitsWindow(QWidget):
    """
    Ekran wprowadzania wizyty i przeglądu poprzednich wizyt,
    zawiera wszystkie pola z tabeli Animal i Appointment.
    """
    navigate = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # --- Wyszukaj opiekuna ---
        self.search_le = QLineEdit()
        self.search_le.setPlaceholderText("🔍 Wyszukaj opiekuna...")
        self.search_le.setStyleSheet(
            "QLineEdit { border:1px solid #ccc; border-radius:20px; padding:8px 12px; font-size:14px; background-color:#fff;}"
            "QLineEdit:focus { border:1px solid #38a2db;}"
        )
        main_layout.addWidget(self.search_le)

        # --- Pasek akcji (Zapisz) ---
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        self.save_btn = QPushButton("Zapisz wizytę")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet(
            "QPushButton { background-color:#38a2db; color:#fff; padding:8px 16px; border:none; border-radius:4px; font-size:14px; }"
            "QPushButton:hover { background-color:#2f8acb; }"
            "QPushButton:pressed { background-color:#277aa8; }"
        )
        action_layout.addWidget(self.save_btn)
        main_layout.addLayout(action_layout)

        # --- Formularz wizyty (Appointment) ---
        form_box = QGroupBox("Nowa wizyta")
        form_box.setStyleSheet(
            "QGroupBox { background-color:#fff; border:1px solid #e0e0e0; border-radius:8px; padding:12px;}"
            "QGroupBox::title { subcontrol-origin:margin; subcontrol-position:top left; padding:0 5px; font-weight:bold; }"
        )
        form_layout = QFormLayout(form_box)
        # pola Appointment
        self.datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_edit.setCalendarPopup(True)
        self.animal_cb = QComboBox()
        self.owner_cb = QComboBox()
        self.status_cb = QComboBox(); self.status_cb.addItems(["zaplanowana","odwołana","zakończona"])
        self.reason_te  = QTextEdit(); self.reason_te.setFixedHeight(60)
        self.notes_te   = QTextEdit(); self.notes_te.setFixedHeight(80)

        form_layout.addRow("Data i czas:",   self.datetime_edit)
        form_layout.addRow("Zwierzę:",         self.animal_cb)
        form_layout.addRow("Właściciel:",      self.owner_cb)
        form_layout.addRow("Status:",          self.status_cb)
        form_layout.addRow("Powód wizyty:",    self.reason_te)
        form_layout.addRow("Uwagi wizyty:",    self.notes_te)
        form_box.setLayout(form_layout)
        main_layout.addWidget(form_box)

        # --- Dane zwierzęcia (Animal) ---
        info_box = QGroupBox("Dane zwierzęcia")
        info_box.setStyleSheet(form_box.styleSheet())
        info_layout = QFormLayout(info_box)
        # pola Animal
        self.species_le     = QLineEdit()
        self.breed_le       = QLineEdit()
        self.gender_le      = QLineEdit()
        self.birthdate_le   = QLineEdit()
        self.age_le         = QLineEdit()
        self.weight_le      = QLineEdit()
        self.microchip_le   = QLineEdit()
        self.animal_notes_te= QTextEdit(); self.animal_notes_te.setFixedHeight(60)

        info_layout.addRow("Gatunek:",        self.species_le)
        info_layout.addRow("Rasa:",           self.breed_le)
        info_layout.addRow("Płeć:",           self.gender_le)
        info_layout.addRow("Data ur.:",       self.birthdate_le)
        info_layout.addRow("Wiek:",           self.age_le)
        info_layout.addRow("Waga (kg):",      self.weight_le)
        info_layout.addRow("Mikroczip:",      self.microchip_le)
        info_layout.addRow("Uwagi zwierzęcia:", self.animal_notes_te)
        main_layout.addWidget(info_box)

        # --- Poprzednie wizyty ---
        prev_box = QGroupBox("Poprzednie wizyty")
        prev_box.setStyleSheet(form_box.styleSheet())
        prev_layout = QVBoxLayout(prev_box)
        self.prev_table = QTableWidget(0, 6)
        self.prev_table.setHorizontalHeaderLabels([
            "Data i czas","Zwierzę","Właściciel","Status","Powód","Uwagi"
        ])
        prev_layout.addWidget(self.prev_table)
        main_layout.addWidget(prev_box)

        # --- Sygnały ---
        self.save_btn.clicked.connect(self._on_save_visit)
        self.animal_cb.currentIndexChanged.connect(self._on_animal_change)

        # --- Dane demo ---
        self._load_animals()
        self._load_previous_visits()

    def _load_animals(self):
        # demo danych z tabeli Animal (ze wszystkimi polami)
        self.animals = {
            1: {"name":"Burek","species":"Pies","breed":"Owczarek","gender":"male","birth_date":"2020-01-05","age":5,"weight":30.0,"microchip":"123ABC","notes":"Brak uwag","owner":"Jan Kowalski"},
            2: {"name":"Mruczek","species":"Kot","breed":"Perski","gender":"female","birth_date":"2019-06-10","age":6,"weight":5.2,"microchip":"","notes":"Alergia pokarmowa","owner":"Anna Nowak"},
        }
        self.animal_cb.clear(); self.owner_cb.clear()
        for aid,info in self.animals.items():
            self.animal_cb.addItem(info["name"],aid)
        self._on_animal_change(0)

    def _on_animal_change(self,index):
        aid  = self.animal_cb.currentData()
        info = self.animals.get(aid,{})
        # wczytaj pola Animal
        self.species_le.setText(str(info.get("species","")))
        self.breed_le.setText(str(info.get("breed","")))
        self.gender_le.setText(str(info.get("gender","")))
        self.birthdate_le.setText(str(info.get("birth_date","")))
        self.age_le.setText(str(info.get("age","")))
        self.weight_le.setText(str(info.get("weight","")))
        self.microchip_le.setText(str(info.get("microchip","")))
        self.animal_notes_te.setPlainText(info.get("notes",""))
        # ustaw owner CB
        owner = info.get("owner","")
        self.owner_cb.addItem(owner, info.get("owner_id",0))

    def _load_previous_visits(self):
        # demo Appointment (wszystkie pola bez doctor_id)
        aid = self.animal_cb.currentData()
        sample = {
            1: [("2025-04-20 09:00","Burek","Jan Kowalski","zakończona","Kontrola szczepienia","Wszystko OK")],
            2: [("2025-04-22 14:00","Mruczek","Anna Nowak","odwołana","Zabieg kleszcza","")],
        }
        visits = sample.get(aid,[])
        self.prev_table.setRowCount(0)
        for rec in visits:
            r = self.prev_table.rowCount(); self.prev_table.insertRow(r)
            for c,val in enumerate(rec):
                self.prev_table.setItem(r,c, QTableWidgetItem(str(val)))

    def _on_save_visit(self):
        dt     = self.datetime_edit.dateTime().toString("yyyy-MM-dd HH:mm")
        aid    = self.animal_cb.currentData()
        owner  = self.owner_cb.currentText()
        status = self.status_cb.currentText()
        reason = self.reason_te.toPlainText()
        notes  = self.notes_te.toPlainText()
        QMessageBox.information(self,"Sukces",
            f"Wizyta ({dt}) dla zwierzęcia ID={aid}, właściciel {owner} zapisana ({status}).")
        self._load_previous_visits()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = VisitsWindow()
    w.show()
    sys.exit(app.exec_())
