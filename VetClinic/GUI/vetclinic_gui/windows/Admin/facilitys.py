from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QLabel, QHeaderView
)
from PyQt5.QtCore import Qt

from vetclinic_gui.services.facility_service import FacilityService

class FacilitiesPage(QWidget):
    """
    Pełny CRUD placówek: przegląd, dodawanie, usuwanie, modyfikacja i zapis zmian.
    """
    def __init__(self, admin_id=None):
        super().__init__()
        self.admin_id = admin_id
        self._deleted_ids = set()
        self._setup_ui()
        self._load_facilities()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Tytuł
        title = QLabel("Zarządzanie placówkami")
        title.setStyleSheet(
            "font-size:18px; font-weight:bold; color:#111827; padding-bottom:8px;"
        )
        layout.addWidget(title)

        # Tabela placówek
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Nazwa", "Adres", "Telefon"])
        self.table.hideColumn(0)                  # ukrywa ID
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setSelectionMode(self.table.SingleSelection)

        # Stylizacja: brak pionowych ramek, cienkie poziome linie
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: #ffffff;
                alternate-background-color: #f9fafb;
            }
            QHeaderView::section {
                background-color: #ffffff;
                padding: 8px 6px;
                font-weight: 600;
                color: #111827;
                border-bottom: 2px solid #e5e7eb;
                border-right: 0px;
            }
            QTableWidget::item {
                border-bottom: 1px solid #e5e7eb;
                border-right: 0px;
                padding: 10px 6px;
                color: #374151;
            }
        """)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        layout.addWidget(self.table)

        # Przyciski
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.add_btn = QPushButton("Dodaj placówkę")
        self.remove_btn = QPushButton("Usuń zaznaczone")
        self.save_btn = QPushButton("Zapisz zmiany")

        for btn in (self.add_btn, self.remove_btn):
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { padding:6px 12px; background-color:#ffffff; "
                "color:#111827; border:1px solid #e5e7eb; border-radius:5px; }"
                "QPushButton:hover { background-color:#f3f4f6; }"
            )
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet(
            "QPushButton { padding:6px 12px; background-color:#38a2db; "
            "color:#ffffff; border:none; border-radius:5px; }"
            "QPushButton:hover { background-color:#2e97c9; }"
        )

        self.add_btn.clicked.connect(self._on_add)
        self.remove_btn.clicked.connect(self._on_remove)
        self.save_btn.clicked.connect(self._on_save)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def _load_facilities(self):
        self.table.setRowCount(0)
        for fac in FacilityService.list():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(fac.id)))
            self.table.setItem(row, 1, QTableWidgetItem(fac.name))
            self.table.setItem(row, 2, QTableWidgetItem(fac.address))
            self.table.setItem(row, 3, QTableWidgetItem(fac.phone or ""))

    def _on_add(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col in range(1, 4):
            self.table.setItem(row, col, QTableWidgetItem(""))

    def _on_remove(self):
        selected_rows = {item.row() for item in self.table.selectedItems()}
        for row in sorted(selected_rows, reverse=True):
            id_item = self.table.item(row, 0)
            if id_item and id_item.text():
                self._deleted_ids.add(int(id_item.text()))
            self.table.removeRow(row)

    def _on_save(self):
        try:
            # Usuń oznaczone
            for fid in self._deleted_ids:
                FacilityService.delete(fid)
            self._deleted_ids.clear()
            # Stwórz/aktualizuj
            for row in range(self.table.rowCount()):
                id_item = self.table.item(row, 0)
                payload = {
                    "name": self.table.item(row, 1).text(),
                    "address": self.table.item(row, 2).text(),
                    "phone": self.table.item(row, 3).text(),
                }
                if id_item and id_item.text():
                    FacilityService.update(int(id_item.text()), payload)
                else:
                    payload["created_by"] = self.admin_id
                    FacilityService.create(payload)
            QMessageBox.information(self, "Sukces", "Zmiany zostały zapisane.")
            self._load_facilities()
        except Exception as e:
            QMessageBox.critical(self, "Błąd zapisu", str(e))
