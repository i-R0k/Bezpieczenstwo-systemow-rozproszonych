import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QGroupBox,
    QLabel, QPushButton, QFrame, QComboBox,
    QTableWidget, QTableWidgetItem,
    QCalendarWidget, QToolButton, QHeaderView,
    QSizePolicy, QToolTip
)
from PyQt5.QtCore import Qt, QDate, QDateTime
from PyQt5.QtGui import (
    QFont, QBrush, QColor, QCursor, QPen,
    QLinearGradient, QGradient, QTextCharFormat, QPainter
)
from PyQt5.QtChart import (
    QChart, QChartView,
    QLineSeries, QAreaSeries, QScatterSeries,
    QDateTimeAxis, QValueAxis
)

from vetclinic_gui.services.medical_records_service import MedicalRecordService
from vetclinic_gui.services.appointments_service    import AppointmentService
from vetclinic_gui.services.animals_service         import AnimalService
from vetclinic_gui.services.blockchain_service import BlockchainService

class DashboardWindow(QMainWindow):
    def __init__(self, client_id: int):
        super().__init__()
        self.client_id = client_id
        self.blockchain = BlockchainService()

        # Pobierz wszystkie zwierzęta klienta
        self.animals = AnimalService.list_by_owner(client_id) or []  # :contentReference[oaicite:4]{index=4}
        self.animal_id = self.animals[0].id if self.animals else None

        # Do śledzenia podświetlonych dni w kalendarzu
        self.highlighted_dates = []
        # Bieżące wizyty dla wybranego zwierzaka
        self.current_appointments = []

        self.setWindowTitle("VetClinic – Dashboard klienta")
        self.setMinimumSize(1080, 720)
        self.showMaximized()

        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Panel główny
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        content_layout.addLayout(self._create_top_bar())
        content_layout.addWidget(self._create_medical_card(), 1)

        # Dolne panele: moduł blockchain + kalendarz wizyt
        bottom = QHBoxLayout()
        bottom.setSpacing(15)
        # Zamiast wykresu wagi: moduł blockchain
        self.bc_group = self._create_blockchain_module()
        bottom.addWidget(self.bc_group, 1)
        bottom.addWidget(self._create_clinic_visits(), 1)
        content_layout.addLayout(bottom, 1)

        main_layout.addWidget(content)


    def _create_top_bar(self):
        layout = QHBoxLayout()

        # ComboBox ze zwierzakami
        self.combo_animal = QComboBox()
        for animal in self.animals:
            self.combo_animal.addItem(animal.name, animal.id)
        self.combo_animal.currentIndexChanged.connect(self.on_animal_changed)
        layout.addWidget(self.combo_animal)

        layout.addStretch()

        appt_btn = QPushButton("Umów wizytę")
        appt_btn.setCursor(Qt.PointingHandCursor)
        appt_btn.setStyleSheet(
            "QPushButton { padding:8px 16px; background-color:#38a2db; color:#fff; "
            "border:none; border-radius:15px; }"
            "QPushButton:hover { background-color:#2e97c9; }"
        )
        layout.addWidget(appt_btn)

        return layout

    def on_animal_changed(self, index: int):
        """Wywoływane przy wyborze innego zwierzaka."""
        self.animal_id = self.combo_animal.currentData()
        self.refresh_data()

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

    def _create_medical_card(self) -> QGroupBox:
        group = QGroupBox("Karta medyczna")
        group.setStyleSheet(self._groupbox_css())
        layout = QVBoxLayout(group)

        # Nagłówek
        hdr = QHBoxLayout()
        lbl = QLabel("Karta medyczna")
        lbl.setFont(QFont('Arial', 12, QFont.Bold))
        hdr.addWidget(lbl); hdr.addStretch()
        btn = QToolButton(); btn.setText("\u22EE"); hdr.addWidget(btn)
        layout.addLayout(hdr)

        # Tabela
        self.med_table = QTableWidget(0, 4)
        self.med_table.setHorizontalHeaderLabels(["Opis", "Data wizyty", "Status", "Notatki"])
        self.med_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.med_table.setSelectionMode(QTableWidget.NoSelection)
        self.med_table.setFrameShape(QFrame.NoFrame)
        self.med_table.setShowGrid(False)
        self.med_table.verticalHeader().setVisible(False)
        self.med_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.med_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.med_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.med_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.med_table.setColumnWidth(3, 20)
        self.med_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.med_table.setStyleSheet("""
            QHeaderView::section {
                background-color: #ffffff; border:none; padding:8px;
                font-weight:600; color:#111827; border-bottom:2px solid #e5e7eb;
            }
            QTableWidget {
                border:none; background:transparent;
            }
            QTableWidget::item {
                border-bottom:1px solid #e5e7eb; padding:10px 6px;
            }
        """)
        layout.addWidget(self.med_table)

        return group

    def _create_clinic_visits(self) -> QGroupBox:
        group = QGroupBox("Wizyty kliniczne")
        group.setStyleSheet(self._groupbox_css())
        layout = QVBoxLayout(group)

        self.clinic_calendar = QCalendarWidget()
        self.clinic_calendar.setFirstDayOfWeek(Qt.Monday)
        layout.addWidget(self.clinic_calendar)

        self.visit_date_lbl = QLabel()
        self.visit_date_lbl.setStyleSheet(
            "color: #38a2db; font-weight: bold; font-size: 14px; padding-left:8px;"
        )
        self.visit_desc_lbl = QLabel()
        self.visit_desc_lbl.setWordWrap(True)
        self.visit_desc_lbl.setStyleSheet("color: #4b5563; font-size:13px; padding:2px 8px;")
        layout.addWidget(self.visit_date_lbl)
        layout.addWidget(self.visit_desc_lbl)

        self.clinic_calendar.selectionChanged.connect(self._clinic_on_date_changed)
        return group

    def refresh_data(self):
        """Pobiera i wyświetla historię wizyt + opisy medyczne dla self.animal_id."""

        # 1) Pobierz wszystkie wizyty tego klienta
        try:
            all_appts = AppointmentService.list_by_owner(self.client_id) or []
        except Exception as e:
            QToolTip.showText(QCursor.pos(), f"Błąd pobierania wizyt: {e}")
            all_appts = []

        # 2) Filtrujemy tylko wizyty dla wybranego zwierzaka
        appts = [a for a in all_appts if a.animal_id == self.animal_id]
        appts.sort(key=lambda a: a.visit_datetime, reverse=True)
        self.current_appointments = appts

        # 3) Wyczyść tabelę
        self.med_table.setRowCount(0)

        # 4) Wypełnij każdy wiersz
        for row, appt in enumerate(appts):
            # pobierz rekordy medyczne dla tej wizyty
            recs = MedicalRecordService.list_by_appointment(appt.id) or []

            # wybierz opis: najpierw z medical_records, w przeciwnym razie z appointment.reason
            if recs:
                desc = " | ".join(r.description for r in recs if r.description)
            else:
                desc = appt.reason or ""

            self.med_table.insertRow(row)

            # kolumna 0: Opis
            item_desc = QTableWidgetItem(desc)
            item_desc.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.med_table.setItem(row, 0, item_desc)

            # kolumna 1: Data wizyty
            dt_str = appt.visit_datetime.strftime("%d.%m.%Y, %H:%M")
            item_dt = QTableWidgetItem(dt_str)
            item_dt.setTextAlignment(Qt.AlignCenter)
            item_dt.setForeground(QBrush(QColor('#F53838')))
            self.med_table.setItem(row, 1, item_dt)

            # kolumna 2: Status / priorytet
            item_status = QTableWidgetItem(appt.priority or "")
            item_status.setTextAlignment(Qt.AlignCenter)
            self.med_table.setItem(row, 2, item_status)

            # kolumna 3: Notatki
            item_notes = QTableWidgetItem(appt.notes or "")
            item_notes.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.med_table.setItem(row, 3, item_notes)

        # — Kalendarz wizyt —
        for d in self.highlighted_dates:
            self.clinic_calendar.setDateTextFormat(d, QTextCharFormat())
        self.highlighted_dates.clear()
        days = {
            QDate(a.visit_datetime.date().year,
                  a.visit_datetime.date().month,
                  a.visit_datetime.date().day)
            for a in appts
        }
        fmt = QTextCharFormat()
        fmt.setBackground(QBrush(QColor(56, 162, 219, 50)))
        for d in days:
            self.clinic_calendar.setDateTextFormat(d, fmt)
        self.highlighted_dates = list(days)
        self._clinic_on_date_changed()
        self._load_blockchain_history()

    def _clinic_on_date_changed(self):
        sel = self.clinic_calendar.selectedDate().toPyDate()
        todays = [a for a in self.current_appointments if a.visit_datetime.date() == sel]
        if not todays:
            self.visit_date_lbl.clear(); self.visit_desc_lbl.clear()
            return
        ap = sorted(todays, key=lambda x: x.visit_datetime)[0]
        self.visit_date_lbl.setText(ap.visit_datetime.strftime("%d.%m.%Y, %H:%M"))
        desc = ap.reason or ""
        doc  = f"Dr {ap.doctor.first_name} {ap.doctor.last_name}"
        self.visit_desc_lbl.setText(f"{desc} — {doc}")

    def _create_blockchain_module(self) -> QGroupBox:
        group = QGroupBox("Historia z blockchaina")
        group.setStyleSheet(self._groupbox_css())
        layout = QVBoxLayout(group)

        self.bc_table = QTableWidget(0, 4)
        self.bc_table.setHorizontalHeaderLabels(["Data", "Lekarz", "Opis", "Tx Hash"])
        self.bc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.bc_table)
        return group

    def _load_blockchain_history(self):
        """
        Ładuje historię medyczną z blockchainu pod konto serwisowe i wyświetla w tabeli.
        """
        # Jeśli brak zwierząt, nic nie rób
        if not self.animals:
            return

        # Spróbuj pobrać historię on-chain dla service_account
        try:
            records = self.blockchain.get_medical_history()
        except ConnectionError as e:
            QToolTip.showText(QCursor.pos(), f"Blockchain error: {e}")
            return
        except Exception as e:
            QToolTip.showText(QCursor.pos(), f"Nie udało się pobrać historii z blockchaina: {e}")
            return

        # Wyczyść tabelę i wypełnij, jeśli mamy rekordy
        self.bc_table.setRowCount(0)
        for row, rec in enumerate(records):
            self.bc_table.insertRow(row)
            # Data
            date_str = rec['date'].strftime("%d.%m.%Y %H:%M")
            self.bc_table.setItem(row, 0, QTableWidgetItem(date_str))
            # Lekarz (owner)
            self.bc_table.setItem(row, 1, QTableWidgetItem(rec['owner']))
            # Hash danych
            self.bc_table.setItem(row, 2, QTableWidgetItem(rec['data_hash']))
            # Tx hash (lub "-")
            tx_hash = rec.get('tx_hash') or "-"
            self.bc_table.setItem(row, 3, QTableWidgetItem(tx_hash))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardWindow(client_id=1)
    window.show()
    sys.exit(app.exec_())