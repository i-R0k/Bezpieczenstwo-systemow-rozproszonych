from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QMessageBox, QLabel
)
from PyQt5.QtCore import Qt

from vetclinic_gui.services.consultant_service import ConsultantService

class ConsultantsPage(QWidget):
    def __init__(self, admin_id=None):
        super().__init__()
        self.admin_id = admin_id
        self._deleted_ids = set()
        self._setup_ui()
        self._load_consultants()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Tytuł
        title = QLabel("Zarządzanie konsultantami")
        title.setStyleSheet(
            "font-size:18px; font-weight:bold; color:#111827; padding-bottom:8px;"
        )
        layout.addWidget(title)

        # Tabela
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Imię", "Nazwisko", "Email", "Hasło"])
        self.table.hideColumn(0)  # ukrywamy kolumnę ID
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setSelectionMode(self.table.SingleSelection)

        # Stylizacja tabeli
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
            }
            QTableWidget::item {
                border-bottom: 1px solid #e5e7eb;
                padding: 10px 6px;
                color: #374151;
            }
        """)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.Stretch)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        layout.addWidget(self.table)

        # Przyciski
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.add_btn = QPushButton("Dodaj konsultanta")
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

    def _load_consultants(self):
        self.table.setRowCount(0)
        consultants = ConsultantService.list()
        for cons in consultants:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(cons.id)))
            self.table.setItem(row, 1, QTableWidgetItem(cons.first_name))
            self.table.setItem(row, 2, QTableWidgetItem(cons.last_name))
            self.table.setItem(row, 3, QTableWidgetItem(cons.email))
            # Hasło zawsze puste w widoku – użytkownik wpisuje tylko przy tworzeniu/zmianie
            self.table.setItem(row, 4, QTableWidgetItem(""))

    def _on_add(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        # nowe wiersze bez ID => do utworzenia
        for col in range(1, 5):
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
            for cid in self._deleted_ids:
                ConsultantService.delete(cid)
            self._deleted_ids.clear()

            # Stwórz lub aktualizuj
            for row in range(self.table.rowCount()):
                id_item = self.table.item(row, 0)
                payload = {
                    "first_name": self.table.item(row, 1).text(),
                    "last_name":  self.table.item(row, 2).text(),
                    "email":      self.table.item(row, 3).text(),
                }
                # jeśli w kolumnie hasło wpisano coś, dodaj do payload
                pwd_item = self.table.item(row, 4)
                if pwd_item and pwd_item.text().strip():
                    payload["password"] = pwd_item.text().strip()

                if id_item and id_item.text():
                    # aktualizacja istniejącego konsultanta
                    ConsultantService.update(int(id_item.text()), payload)
                else:
                    # nowy konsultant
                    payload["role"] = "konsultant"
                    ConsultantService.create(payload)

            QMessageBox.information(self, "Sukces", "Zmiany zostały zapisane.")
            self._load_consultants()
        except Exception as e:
            QMessageBox.critical(self, "Błąd zapisu", str(e))
