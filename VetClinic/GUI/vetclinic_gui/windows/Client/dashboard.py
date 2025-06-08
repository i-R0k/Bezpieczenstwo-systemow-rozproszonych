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
from vetclinic_gui.services.weight_logs_service import WeightLogService



class DashboardWindow(QMainWindow):
    def __init__(self, client_id: int):
        super().__init__()
        self.client_id = client_id

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

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Pasek akcji + wybór zwierzaka
        content_layout.addLayout(self._create_top_bar())

        # Karta medyczna
        content_layout.addWidget(self._create_medical_card(), 1)

        # Dolne panele: wykres wagi + kalendarz wizyt
        bottom = QHBoxLayout()
        bottom.setSpacing(15)
        bottom.addWidget(self._create_weight_chart(), 1)
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
        group = QGroupBox("Historia wizyt")
        group.setStyleSheet(self._groupbox_css())
        layout = QVBoxLayout(group)

        # ——— Nagłówek ———
        hdr = QHBoxLayout()
        lbl = QLabel("Historia wizyt")
        lbl.setFont(QFont('Arial', 12, QFont.Bold))
        hdr.addWidget(lbl)
        hdr.addStretch()
        layout.addLayout(hdr)

        # ——— Tabela ———
        self.med_table = QTableWidget(0, 4)
        self.med_table.setHorizontalHeaderLabels([
            "Powód",       # <— zmienione z „Notatki”
            "Priorytet",
            "Leczenie",
            "Data wizyty"
        ])
        self.med_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.med_table.setSelectionMode(QTableWidget.NoSelection)
        self.med_table.setFocusPolicy(Qt.NoFocus)
        self.med_table.setWordWrap(True)
        self.med_table.setShowGrid(False)
        self.med_table.setAlternatingRowColors(True)

        self.med_table.setStyleSheet("""
            QHeaderView::section {
                background-color: #f5f7fa;
                color: #444;
                padding: 8px;
                font-weight: bold;
                border: none;
                border-bottom: 2px solid #e5e7eb;
            }
            QTableWidget {
                background-color: #ffffff;
                gridline-color: #e5e7eb;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e5e7eb;
            }
            QTableWidget::item:selected {
                background-color: #eef4fb;
            }
        """)

        header = self.med_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)           # Powód
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Priorytet
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Leczenie
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Data wizyty

        # Pionowy scroll; poziomy wyłączony
        self.med_table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.med_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        layout.addWidget(self.med_table)
        return group

    def refresh_data(self):
        """Pobiera wizyty, wypełnia tabelę 'Historia wizyt', wykres wagi i kalendarz."""

        try:
            all_appts = AppointmentService.list_by_owner(self.client_id) or []
        except Exception as e:
            QToolTip.showText(QCursor.pos(), f"Błąd pobierania wizyt: {e}")
            all_appts = []

        # 2) Filtrowanie tylko wizyt wybranego zwierzaka
        appts = [a for a in all_appts if a.animal_id == self.animal_id]

        self.med_table.setRowCount(0)
        for row, appt in enumerate(appts):
            self.med_table.insertRow(row)

            # Powód (reason)
            itm_reason = QTableWidgetItem(appt.reason or "")
            itm_reason.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            self.med_table.setItem(row, 0, itm_reason)

            # Priorytet
            itm_prio = QTableWidgetItem(appt.priority or "")
            itm_prio.setTextAlignment(Qt.AlignCenter)
            self.med_table.setItem(row, 1, itm_prio)

            # Leczenie
            itm_treat = QTableWidgetItem(appt.treatment or "")
            itm_treat.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            self.med_table.setItem(row, 2, itm_treat)

            # Data wizyty
            dt = appt.visit_datetime.strftime("%d.%m.%Y\n%H:%M")
            itm_date = QTableWidgetItem(dt)
            itm_date.setTextAlignment(Qt.AlignCenter)
            self.med_table.setItem(row, 3, itm_date)

        self.med_table.resizeRowsToContents()

        try:
            logs = WeightLogService.list_by_animal(self.animal_id) or []
        except Exception as e:
            QToolTip.showText(QCursor.pos(), f"Błąd pobierania historii wag: {e}")
            logs = []

        # przygotuj punkty (timestamp_ms, waga_g)
        pts = sorted(
            [
                (int(w.logged_at.timestamp() * 1000), w.weight * 1000)
                for w in logs
                if w.weight is not None
            ],
            key=lambda x: x[0]
        )

        if pts:
            self._update_weight_chart(pts)

    def _create_weight_chart(self) -> QGroupBox:
        group = QGroupBox("Waga zwierzaka")
        group.setStyleSheet(self._groupbox_css())
        layout = QVBoxLayout(group)

        chart = QChart()
        chart.setBackgroundVisible(False)
        chart.legend().hide()

        # puste serie – uzupełni je _update_weight_chart
        top     = QLineSeries()
        base    = QLineSeries()
        area    = QAreaSeries(top, base)
        scatter = QScatterSeries()

        # gradient wypełnienia
        grad = QLinearGradient(0, 0, 0, 1)
        grad.setCoordinateMode(QGradient.ObjectBoundingMode)
        grad.setColorAt(0.0, QColor(56,162,219,120))
        grad.setColorAt(1.0, QColor(56,162,219,20))
        area.setBrush(QBrush(grad))
        area.setPen(QPen(Qt.NoPen))

        scatter.setMarkerSize(6)
        scatter.setColor(QColor("#38A2DB"))
        scatter.setBorderColor(QColor("#ffffff"))

        axisX = QDateTimeAxis()
        axisX.setFormat("dd.MM.yyyy")
        axisX.setTitleText("Data")
        axisY = QValueAxis()
        axisY.setTitleText("Waga [g]")

        for s in (area, top, scatter):
            chart.addSeries(s)
            s.attachAxis(axisX)
            s.attachAxis(axisY)

        chart.addAxis(axisX, Qt.AlignBottom)
        chart.addAxis(axisY, Qt.AlignLeft)

        view = QChartView(chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(view)

        # referencje do późniejszej aktualizacji
        group._chart   = chart
        group._top     = top
        group._base    = base
        group._area    = area
        group._scatter = scatter
        group._axisX   = axisX
        group._axisY   = axisY
        group._view    = view

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
        """Pobiera dane dla self.animal_id i odświeża UI."""

        try:
            all_appts = AppointmentService.list_by_owner(self.client_id) or []
        except Exception as e:
            QToolTip.showText(QCursor.pos(), f"Błąd pobierania wizyt: {e}")
            all_appts = []

        appts = [a for a in all_appts if a.animal_id == self.animal_id]

        self.med_table.setRowCount(0)
        for row, appt in enumerate(appts):
            self.med_table.insertRow(row)
            # Notatki
            itm_notes = QTableWidgetItem(appt.notes or "")
            itm_notes.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            self.med_table.setItem(row, 0, itm_notes)
            # Priorytet
            itm_prio = QTableWidgetItem(appt.priority or "")
            itm_prio.setTextAlignment(Qt.AlignCenter)
            self.med_table.setItem(row, 1, itm_prio)
            # Leczenie
            itm_treat = QTableWidgetItem(appt.treatment or "")
            itm_treat.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            self.med_table.setItem(row, 2, itm_treat)
            # Data wizyty
            dt = appt.visit_datetime.strftime("%d.%m.%Y\n%H:%M")
            itm_date = QTableWidgetItem(dt)
            itm_date.setTextAlignment(Qt.AlignCenter)
            self.med_table.setItem(row, 3, itm_date)

    def _update_weight_chart(self, pts):
        """Aktualizuje QChart we właściwościach self._create_weight_chart()."""
        # Funkcja Catmull-Rom do wygładzania
        def catmull_rom(points, samples=20):
            def CR(p0, p1, p2, p3, t):
                a = 2*p1[1]
                b = -p0[1] + p2[1]
                c = 2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]
                d = -p0[1] + 3*p1[1] - 3*p2[1] + p3[1]
                ax = 2*p1[0]
                bx = -p0[0] + p2[0]
                cx = 2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]
                dx = -p0[0] + 3*p1[0] - 3*p2[0] + p3[0]
                t2, t3 = t*t, t*t*t
                x = 0.5 * (ax + bx*t + cx*t2 + dx*t3)
                y = 0.5 * (a  + b*t  + c*t2  + d*t3)
                return x, y

            dense = []
            n = len(points)
            if n < 2:
                return points
            for i in range(n-1):
                p0 = points[i-1] if i > 0 else points[i]
                p1, p2 = points[i], points[i+1]
                p3 = points[i+2] if i+2 < n else p2
                for s in range(samples):
                    dense.append(CR(p0, p1, p2, p3, s/samples))
            dense.append(points[-1])
            return dense

        # Przygotuj punkty gęste i surowe
        raw = pts
        dense = catmull_rom(raw)
        weights = [w for _, w in raw]
        mn, mx = min(weights), max(weights)
        dy = (mx - mn) * 0.1 if mx != mn else mx*0.1
        y_max = mx + dy

        # Wyczyść stare serie
        chart   = self._create_weight_chart.__self__._chart
        top     = self._create_weight_chart.__self__._top
        base    = self._create_weight_chart.__self__._base
        area    = self._create_weight_chart.__self__._area
        scatter = self._create_weight_chart.__self__._scatter
        axisX   = self._create_weight_chart.__self__._axisX
        axisY   = self._create_weight_chart.__self__._axisY

        top.clear(); base.clear(); scatter.clear()
        chart.removeAllSeries()

        # Nowe serie
        for x, y in dense:
            top.append(x, y)
            base.append(x, 0)

        pen = QPen(QColor("#38A2DB"))
        pen.setWidth(2)
        top.setPen(pen)

        new_area = QAreaSeries(top, base)
        grad = QLinearGradient(0, 0, 0, 1)
        grad.setCoordinateMode(QGradient.ObjectBoundingMode)
        grad.setColorAt(0.0, QColor(56,162,219,120))
        grad.setColorAt(1.0, QColor(56,162,219,20))
        new_area.setBrush(QBrush(grad))
        new_area.setPen(QPen(Qt.NoPen))

        new_scatter = QScatterSeries()
        new_scatter.setMarkerSize(6)
        new_scatter.setColor(QColor("#38A2DB"))
        new_scatter.setBorderColor(QColor("#ffffff"))
        for x, y in raw:
            new_scatter.append(x, y)

        # ToolTip
        def show_tt(pt, state):
            if state:
                dt = QDateTime.fromMSecsSinceEpoch(int(pt.x())).date().toString("dd.MM.yyyy")
                QToolTip.showText(QCursor.pos(), f"{dt}: {int(pt.y())} g")
        new_scatter.hovered.connect(show_tt)

        # Dodajemy serie
        for series in (new_area, top, new_scatter):
            chart.addSeries(series)
            series.attachAxis(axisX)
            series.attachAxis(axisY)

        axisY.setRange(0, y_max)
        chart.addAxis(axisX, Qt.AlignBottom)
        chart.addAxis(axisY, Qt.AlignLeft)
        self._create_weight_chart.__self__._view.repaint()

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardWindow(client_id=1)
    window.show()
    sys.exit(app.exec_())