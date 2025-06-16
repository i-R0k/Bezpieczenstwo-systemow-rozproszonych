from datetime import datetime
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QLabel, QSizePolicy
)
from PyQt5.QtGui import QBrush, QColor, QFont
from vetclinic_gui.services.invoice_service import InvoiceService

class InvoicesWindow(QWidget):
    def __init__(self, client_id: int):
        super().__init__()
        self.client_id = client_id
        self.setWindowTitle("Faktury klienta")
        self.resize(800, 600)
        self._setup_ui()
        self._load_invoices()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # Tytuł sekcji
        title = QLabel("Lista faktur")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        root.addWidget(title)

        # Grupa z tabelą
        box = QGroupBox()
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, 4)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #f7f7f7;
                padding: 6px;
                border-bottom: 1px solid #dcdcdc;
                font-weight: bold;
            }
        """)

        headers = ["ID", "Data wystawienia", "Kwota", "Status"]
        self.table.setHorizontalHeaderLabels(headers)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(24)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        box_layout.addWidget(self.table)
        root.addWidget(box)

        # Etykieta gdy brak faktur
        self.empty_label = QLabel("Brak faktur do wyświetlenia.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #888; font-style: italic;")
        root.addWidget(self.empty_label)

    def _load_invoices(self):
        try:
            invoices = InvoiceService.list_by_client(self.client_id) or []
        except Exception:
            invoices = []

        invoices.sort(key=lambda inv: getattr(inv, "created_at", datetime.min), reverse=True)
        self.table.setRowCount(0)

        if not invoices:
            self.table.hide()
            self.empty_label.show()
            return

        self.empty_label.hide()
        self.table.show()

        for row, inv in enumerate(invoices):
            self.table.insertRow(row)

            # ID
            id_val = getattr(inv, "id", "")
            id_item = QTableWidgetItem(str(id_val))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, id_item)

            # Data wystawienia
            raw = getattr(inv, "created_at", "")
            if isinstance(raw, str):
                try:
                    dt = datetime.fromisoformat(raw)
                except:
                    dt = None
            else:
                dt = raw
            if dt:
                date_str = dt.strftime("%d.%m.%Y")
            else:
                date_str = ""
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignCenter)
            date_item.setForeground(QBrush(QColor('#d32f2f')))
            self.table.setItem(row, 1, date_item)

            # Kwota
            amt_raw = getattr(inv, "amount", "")
            try:
                amt = float(amt_raw)
                amt_str = f"{amt:,.2f} PLN"
            except:
                amt_str = str(amt_raw)
            amt_item = QTableWidgetItem(amt_str)
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, amt_item)

            # Status
            status = getattr(inv, "status", "")
            status_item = QTableWidgetItem(status.capitalize())
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, status_item)
