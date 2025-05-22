from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QMessageBox, QLabel, QLineEdit
)
from PyQt5.QtCore import Qt

from vetclinic_gui.services.doctors_service import DoctorService

class DoctorsPage(QWidget):
    """
    Pełny CRUD lekarzy: przegląd, dodawanie, usuwanie, modyfikacja i zapis zmian.
    Stylizacja zgodna z ConsultantsPage i FacilitiesPage.
    """
    def __init__(self, admin_id=None):
        super().__init__()
        self.admin_id = admin_id
        self._deleted_ids = set()
        self._setup_ui()
        self._load_doctors()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Nagłówek
        title = QLabel("Zarządzanie lekarzami")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1F2937;
            padding-bottom: 12px;
        """)
        layout.addWidget(title)

        # Tabela: 6 kolumn (ID ukryte, Imię, Nazwisko, Email, Specjalizacja, Nr pozwolenia)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Imię", "Nazwisko", "Email",
            "Specjalizacja", "Nr pozw."
        ])
        self.table.hideColumn(0)

        # Stała wysokość wiersza i ukryty pionowy nagłówek
        vh = self.table.verticalHeader()
        vh.setVisible(False)
        vh.setSectionResizeMode(QHeaderView.Fixed)
        vh.setDefaultSectionSize(48)

        # Pozostałe ustawienia
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        # Stylizacja
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                alternate-background-color: #F9FAFB;
                gridline-color: #E5E7EB;
            }
            QHeaderView::section {
                background-color: #F3F4F6;
                padding: 10px;
                font-size: 14px;
                font-weight: 600;
                color: #374151;
                border: 1px solid #E5E7EB;
            }
            QTableWidget::item {
                padding: 8px;
                color: #1F2937;
            }
            QLineEdit {
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 4px 6px;
            }
        """)

        # Proporcje kolumn
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)         # Imię
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)         # Nazwisko
        hdr.setSectionResizeMode(3, QHeaderView.Stretch)         # Email
        hdr.setSectionResizeMode(4, QHeaderView.Stretch)         # Specjalizacja
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents) # Nr pozwolenia
        hdr.setStretchLastSection(False)

        layout.addWidget(self.table)

        # Przyciski
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.add_btn    = QPushButton("Dodaj lekarza")
        self.remove_btn = QPushButton("Usuń zaznaczone")
        self.save_btn   = QPushButton("Zapisz zmiany")

        for btn in (self.add_btn, self.remove_btn):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(32)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    color: #374151;
                    border: 1px solid #D1D5DB;
                    border-radius: 4px;
                    padding: 0 12px;
                }
                QPushButton:hover {
                    background-color: #F3F4F6;
                }
            """)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setFixedHeight(32)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)

        self.add_btn.clicked.connect(self._on_add)
        self.remove_btn.clicked.connect(self._on_remove)
        self.save_btn.clicked.connect(self._on_save)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def _load_doctors(self):
        self.table.setRowCount(0)
        doctors = DoctorService.list() or []

        for doc in doctors:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(doc.id)))

            # Imię, Nazwisko, Email
            for col, value in ((1, doc.first_name),
                               (2, doc.last_name),
                               (3, doc.email)):
                le = QLineEdit(value or "")
                le.setFixedHeight(28)
                self.table.setCellWidget(row, col, le)

            # Specjalizacja (getattr zabezpiecza brak pola)
            spec = getattr(doc, "specialization", "")
            spec_le = QLineEdit(spec)
            spec_le.setFixedHeight(28)
            self.table.setCellWidget(row, 4, spec_le)

            # Numer pozwolenia
            permit = getattr(doc, "permit_number", "")
            permit_le = QLineEdit(permit)
            permit_le.setFixedHeight(28)
            self.table.setCellWidget(row, 5, permit_le)

    def _on_add(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Imię, Nazwisko, Email, Specjalizacja, Nr pozwolenia
        placeholders = {
            1: "Imię",
            2: "Nazwisko",
            3: "Email",
            4: "Specjalizacja",
            5: "Nr pozwolenia"
        }
        for col in (1, 2, 3, 4, 5):
            le = QLineEdit()
            le.setFixedHeight(28)
            le.setPlaceholderText(placeholders[col])
            self.table.setCellWidget(row, col, le)

    def _on_remove(self):
        rows = {item.row() for item in self.table.selectedItems()}
        for row in sorted(rows, reverse=True):
            id_item = self.table.item(row, 0)
            if id_item and id_item.text():
                self._deleted_ids.add(int(id_item.text()))
            self.table.removeRow(row)

    def _on_save(self):
        try:
            # Usuń zaznaczonych
            for did in self._deleted_ids:
                DoctorService.delete(did)
            self._deleted_ids.clear()

            # Przetworzenie wierszy
            for row in range(self.table.rowCount()):
                id_item = self.table.item(row, 0)
                is_update = bool(id_item and id_item.text())

                # Pobierz wartości z QLineEdit
                first_le  = self.table.cellWidget(row, 1)
                last_le   = self.table.cellWidget(row, 2)
                email_le  = self.table.cellWidget(row, 3)
                spec_le   = self.table.cellWidget(row, 4)
                permit_le = self.table.cellWidget(row, 5)

                payload = {
                    "first_name":    first_le .text().strip() if first_le  else "",
                    "last_name":     last_le  .text().strip() if last_le   else "",
                    "email":         email_le .text().strip() if email_le  else "",
                    "specialization": spec_le .text().strip() if spec_le   else "",
                    "permit_number": permit_le.text().strip() if permit_le else "",
                }

                if is_update:
                    DoctorService.update(int(id_item.text()), payload)
                else:
                    DoctorService.create(payload)

            QMessageBox.information(self, "Sukces", "Zmiany zostały zapisane.")
            self._load_doctors()

        except Exception as e:
            QMessageBox.critical(self, "Błąd zapisu", str(e))
