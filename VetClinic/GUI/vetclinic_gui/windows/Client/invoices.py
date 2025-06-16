from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QToolTip
)
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
        main = QVBoxLayout(self)

        # pasek akcji: przycisk powrotu
        bar = QHBoxLayout()
        bar.addStretch()
        main.addLayout(bar)

        # tabela faktur
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Data wystawienia", "Kwota", "Status"]
        )
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        main.addWidget(self.table)

    def _load_invoices(self):
        try:
            invoices = InvoiceService.list_by_owner(self.client_id)
        except Exception as e:
            QToolTip.showText(self.mapToGlobal(self.pos()), f"Błąd pobierania faktur: {e}")
            invoices = []

        self.table.setRowCount(0)
        for inv in invoices:
            row = self.table.rowCount(); self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(inv.id)))
            date_str = inv.issue_date.strftime("%d.%m.%Y")
            self.table.setItem(row, 1, QTableWidgetItem(date_str))
            amount = f"{inv.amount:.2f} {inv.currency}"
            self.table.setItem(row, 2, QTableWidgetItem(amount))
            self.table.setItem(row, 3, QTableWidgetItem(inv.status))
