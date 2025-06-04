import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QGroupBox,
    QLabel, QPushButton, QLineEdit, QFrame,
    QTableWidget, QTableWidgetItem,
    QCalendarWidget, QToolButton, QHeaderView,
    QSizePolicy, QSplitter, QToolTip
)
from PyQt5.QtCore import Qt, QDate, QDateTime
from PyQt5.QtGui import QFont, QPainter, QBrush, QColor, QCursor, QPen, QLinearGradient, QGradient
from PyQt5.QtChart import (
    QChart, QChartView,
    QLineSeries, QSplineSeries, QAreaSeries,
    QScatterSeries, QCategoryAxis, QValueAxis, QDateTimeAxis
)

class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VetClinic Dashboard")
        self.setMinimumSize(1080, 720)
        self.showMaximized()

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Usunięty pasek nawigacji – zostawiamy tylko zawartość
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        top_bar = self._create_top_bar()
        content_layout.addLayout(top_bar)

        top_panels = QHBoxLayout()
        top_panels.setSpacing(15)

        med_group = self._create_medical_card()
        vac_group = self._create_vaccinations()

        for w in (med_group, vac_group):
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            w.setMinimumWidth(0)

        top_panels.addWidget(med_group, 1)
        top_panels.addWidget(vac_group,  1)
        content_layout.addLayout(top_panels, 1)

        bottom_panels = QHBoxLayout()
        bottom_panels.setSpacing(15)

        wt = self._create_weight_chart()
        cv = self._create_clinic_visits()

        for w in (wt, cv):
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            w.setMinimumWidth(0)

        bottom_panels.addWidget(wt, 1)
        bottom_panels.addWidget(cv, 1)
        content_layout.addLayout(bottom_panels, 1)

        main_layout.addWidget(content)

    def _create_top_bar(self):
        layout = QHBoxLayout()
        layout.addStretch()
        appt = QPushButton("Umów wizytę")
        appt.setCursor(Qt.PointingHandCursor)
        appt.setStyleSheet(
            "QPushButton { padding:8px 16px; background-color:#38a2db; color:#fff; border:none; border-radius:15px; }"
            "QPushButton:hover { background-color:#2e97c9; }"
        )
        layout.addWidget(appt)
        return layout

    def _create_medical_card(self) -> QGroupBox:
        group = QGroupBox()
        group.setStyleSheet("""
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
        """)

        layout = QVBoxLayout(group)
        header = QHBoxLayout()
        title = QLabel("Karta medyczna")
        title.setFont(QFont('Arial', 12, QFont.Bold))
        header.addWidget(title)
        header.addStretch()
        menu_btn = QToolButton()
        menu_btn.setText("\u22EE")
        menu_btn.setStyleSheet(
            "QToolButton { border:none; font-size:16px; color:#6b7280; }"
            "QToolButton:hover { color:#111827; }"
        )
        header.addWidget(menu_btn)
        layout.addLayout(header)

        table = QTableWidget(4, 4)
        table.setHorizontalHeaderLabels(["Rozpoznanie", "Leczenie", "Data kontroli", ""])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)
        table.setWordWrap(True)
        table.setFrameShape(QFrame.NoFrame)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)

        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        table.setColumnWidth(3, 20)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: transparent;
            }
            QHeaderView::section {
                background-color: #ffffff;
                border: none;
                padding: 8px;
                font-weight: 600;
                color: #111827;
                border-bottom: 2px solid #e5e7eb;
            }
            QTableWidget::item {
                border-bottom: 1px solid #e5e7eb;
                padding: 10px 6px;
            }
        """)

        vsb = table.verticalScrollBar()
        vsb.setStyleSheet("""
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.15);
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::sub-line, QScrollBar::add-line {
                height: 0px;
            }
            QScrollBar::add-page, QScrollBar::sub-page {
                background: transparent;
            }
        """)

        data = [
            ("Zapalenie płuc",     "Augmentin 250mg, 2× dziennie…",    "30.11.2020"),
            ("Awitaminoza",        "Witamina D 1000 IU raz w tygodniu", "28.11.2020"),
            ("Świąd alergiczny",   "Maść Dermatix na zmiany skórne",   "20.05.2020"),
            ("Rana cięta",         "Przemyć chlorheksydyną, kontrola 7 dni", "06.06.2020"),
        ]
        for r, (diag, tx, date) in enumerate(data):
            table.setItem(r, 0, QTableWidgetItem(diag))
            itm = QTableWidgetItem(tx)
            itm.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            table.setItem(r, 1, itm)
            itm_date = QTableWidgetItem(date)
            itm_date.setForeground(QBrush(QColor('#F53838')))
            table.setItem(r, 2, itm_date)
            arrow = QTableWidgetItem("›")
            arrow.setTextAlignment(Qt.AlignCenter)
            arrow.setForeground(QBrush(QColor('#38a2db')))
            table.setItem(r, 3, arrow)

        layout.addWidget(table)
        return group

    def _create_vaccinations(self) -> QGroupBox:
        group = QGroupBox()
        group.setStyleSheet("""
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
        """)

        layout = QVBoxLayout(group)

        header = QHBoxLayout()
        title = QLabel("Szczepienia")
        title.setFont(QFont('Arial', 12, QFont.Bold))
        header.addWidget(title)
        header.addStretch()
        menu_btn = QToolButton()
        menu_btn.setText("\u22EE")
        menu_btn.setStyleSheet(
            "QToolButton { border:none; font-size:16px; color:#6b7280; }"
            "QToolButton:hover { color:#111827; }"
        )
        header.addWidget(menu_btn)
        layout.addLayout(header)

        table = QTableWidget(6, 5)
        table.setHorizontalHeaderLabels([
            "Choroba", "Status", "Szczepionka", "Pierwotne", "Powtórka"
        ])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)
        table.setWordWrap(True)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)

        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: transparent;
            }
            QHeaderView::section {
                background-color: #ffffff;
                border: none;
                padding: 8px;
                font-weight: 600;
                color: #111827;
                border-bottom: 2px solid #e5e7eb;
            }
            QTableWidget::item {
                border-bottom: 1px solid #e5e7eb;
                padding: 10px 6px;
            }
        """)

        vsb = table.verticalScrollBar()
        vsb.setStyleSheet("""
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.15);
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::sub-line, QScrollBar::add-line {
                height: 0px;
            }
            QScrollBar::add-page, QScrollBar::sub-page {
                background: transparent;
            }
        """)

        vac_data = [
            ("Wścieklizna",       "Zrobione",     "Nobivac DHP",   "21.03.2020", "07.07.2020"),
            ("Zapalenie wątroby", "Do zrobienia", "Nobivac DHPPi","07.07.2020", "25.11.2020"),
            ("Dżuma",             "Do zrobienia", "Nobivac DHPPi","07.07.2020", "25.11.2020"),
            ("Parwowiroza",       "Zrobione",     "Nobivac DHP",   "21.03.2020", "07.07.2020"),
            ("Parainfluenza",     "Do zrobienia", "Nobivac KC",    "13.12.2020", "Raz"),
            ("Leptospiroza",      "Zrobione",     "Nobivac Lepto4","05.12.2019", "Raz"),
        ]
        for r, (c, s, v, p, rep) in enumerate(vac_data):
            table.setItem(r, 0, QTableWidgetItem(c))
            table.setItem(r, 1, QTableWidgetItem(s))
            table.setItem(r, 2, QTableWidgetItem(v))
            table.setItem(r, 3, QTableWidgetItem(p))
            table.setItem(r, 4, QTableWidgetItem(rep))

        layout.addWidget(table)
        return group

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

    def _create_weight_chart(self) -> QGroupBox:
        group = QGroupBox("Waga zwierzaka")
        group.setStyleSheet(self._groupbox_css())
        layout = QVBoxLayout(group)

        header = QHBoxLayout()
        title = QLabel("Waga zwierzaka")
        title.setFont(QFont('Arial', 12, QFont.Bold))
        header.addWidget(title)
        header.addStretch()
        menu_btn = QToolButton()
        menu_btn.setText("\u22EE")
        menu_btn.setStyleSheet(
            "QToolButton { border:none; font-size:16px; color:#6b7280; }"
            "QToolButton:hover { color:#111827; }"
        )
        header.addWidget(menu_btn)
        layout.addLayout(header)

        # 1) Dane: waga + odpowiadające im dni pierwszego każdego miesiąca
        weights = [2000, 2500, 2300, 2400, 2600, 2800, 3000, 3200, 3100, 3000, 2900, 2800]
        dates   = [QDate(2025, m, 1) for m in range(1, 13)]

        # 2) Zakres Y
        mn, mx = min(weights), max(weights)
        dy = (mx - mn) * 0.1
        y_min, y_max = mn - dy, mx + dy

        # 3) Rzut na timestamp i Catmull–Rom densyfikacja
        raw_pts = [(QDateTime(d).toMSecsSinceEpoch(), w) for d, w in zip(dates, weights)]
        def catmull_rom(pts, samples=20):
            def CR(p0,p1,p2,p3,t):
                a = 2*p1[1]
                b = -p0[1] + p2[1]
                c = 2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]
                d = -p0[1] + 3*p1[1] - 3*p2[1] + p3[1]
                ax = 2*p1[0]
                bx = -p0[0] + p2[0]
                cx = 2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]
                dx = -p0[0] + 3*p1[0] - 3*p2[0] + p3[0]
                t2, t3 = t*t, t*t*t
                y = 0.5*(a + b*t + c*t2 + d*t3)
                x = 0.5*(ax + bx*t + cx*t2 + dx*t3)
                return x, y

            dense = []
            n = len(pts)
            for i in range(n-1):
                p0 = pts[i-1] if i-1>=0 else pts[i]
                p1, p2 = pts[i], pts[i+1]
                p3 = pts[i+2] if i+2<n else pts[i+1]
                for s in range(samples):
                    dense.append(CR(p0, p1, p2, p3, s/ samples))
            dense.append(pts[-1])
            return dense

        dense_pts = catmull_rom(raw_pts, samples=20)

        # 4) Tworzymy gęstą linię i bazę(y=0)
        top = QLineSeries()
        for x, y in dense_pts:
            top.append(x, y)
        pen = QPen(QColor("#38A2DB"))
        pen.setWidth(2); pen.setCapStyle(Qt.RoundCap); pen.setJoinStyle(Qt.RoundJoin)
        top.setPen(pen)

        base = QLineSeries()
        for x, _ in dense_pts:
            base.append(x, 0)

        # 5) Obszar z gradientowym wypełnieniem
        area = QAreaSeries(top, base)
        grad = QLinearGradient(0, 0, 0, 1)
        grad.setCoordinateMode(QGradient.ObjectBoundingMode)
        grad.setColorAt(0.0, QColor(56,162,219,120))
        grad.setColorAt(1.0, QColor(56,162,219,20))
        area.setBrush(QBrush(grad))
        area.setPen(QPen(Qt.NoPen))

        # 6) Scatter oryginalnych punktów
        scatter = QScatterSeries()
        scatter.setMarkerSize(8)
        scatter.setColor(QColor("#38A2DB"))
        scatter.setBorderColor(QColor("#ffffff"))
        for d, w in zip(dates, weights):
            scatter.append(QDateTime(d).toMSecsSinceEpoch(), w)

        def show_tt(pt, state):
            if state:
                dt = QDateTime.fromMSecsSinceEpoch(int(pt.x())).date().toString("MMM yyyy")
                QToolTip.showText(QCursor.pos(), f"{dt}: {int(pt.y())} g")
        scatter.hovered.connect(show_tt)

        # 7) Budujemy QChart
        chart = QChart()
        chart.addSeries(area)
        chart.addSeries(top)
        chart.addSeries(scatter)
        chart.setBackgroundVisible(False)
        chart.legend().hide()

        # 8) Oś X datowa
        axisX = QDateTimeAxis()
        axisX.setFormat("MMM")
        axisX.setTitleText("Miesiąc")
        axisX.setTickCount(len(dates))
        axisX.setRange(
            QDateTime(dates[0]),
            QDateTime(dates[-1].addMonths(1))
        )
        chart.addAxis(axisX, Qt.AlignBottom)
        for s in (area, top, scatter):
            s.attachAxis(axisX)

        # 9) Oś Y
        axisY = QValueAxis()
        axisY.setRange(0, y_max)
        axisY.setLabelFormat("%d")
        axisY.setTitleText("Waga [g]")
        chart.addAxis(axisY, Qt.AlignLeft)
        for s in (area, top, scatter):
            s.attachAxis(axisY)

        # 10) View i porządkowanie GC
        view = QChartView(chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        view.setStyleSheet("border:none; background-color:transparent;")
        layout.addWidget(view)

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
        group = QGroupBox()
        group.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 16px;
            }
        """)

        layout = QVBoxLayout(group)
        header = QHBoxLayout()
        title = QLabel("Wizyty kliniczne")
        title.setFont(QFont('Arial', 12, QFont.Bold))
        header.addWidget(title)
        header.addStretch()
        menu_btn = QToolButton()
        menu_btn.setText("\u22EE")
        menu_btn.setStyleSheet(
            "QToolButton { border:none; font-size:16px; color:#6b7280; }"
            "QToolButton:hover { color:#111827; }"
        )
        header.addWidget(menu_btn)
        layout.addLayout(header)

        cal = QCalendarWidget()
        cal.setFirstDayOfWeek(Qt.Monday)
        cal.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        cal.setHorizontalHeaderFormat(QCalendarWidget.ShortDayNames)
        cal.setNavigationBarVisible(True)
        cal.setGridVisible(False)
        cal.setStyleSheet("""
            QCalendarWidget {
                background-color: transparent;
                border: none;
            }
            QCalendarWidget QToolButton {
                margin: 4px;
                color: #111827;
                font-size: 14px;
                font-weight: bold;
            }
            QCalendarWidget QSpinBox {
                width: 100px;
                font-size: 14px;
                font-weight: bold;
                color: #111827;
                background: transparent;
                border: none;
            }
            QCalendarWidget QSpinBox::up-button,
            QCalendarWidget QSpinBox::down-button {
                width: 0; height: 0;
            }
            QCalendarWidget QAbstractItemView {
                selection-background-color: #38a2db;
                selection-color: white;
                outline: none;
                font-size: 12px;
            }
            QCalendarWidget QAbstractItemView::item {
                border-radius: 4px;
                height: 28px;
                width: 28px;
                margin: 2px;
            }
            QCalendarWidget QAbstractItemView::item:hover {
                background: rgba(56,162,219,0.1);
            }
            QCalendarWidget QAbstractItemView::item:selected {
                background: #38a2db;
                color: white;
            }
        """)
        layout.addWidget(cal)

        date_lbl = QLabel("18.11.2020, 16:30")
        date_lbl.setStyleSheet(
            "color: #38a2db;"
            "font-weight: bold;"
            "font-size: 14px;"
            "padding-left: 8px;"
        )
        desc_lbl = QLabel("Kontrola i szczepienie, Dr. Petrikov V.V., pok.206")
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(
            "color: #4b5563;"
            "font-size: 13px;"
            "padding: 2px 8px;"
        )
        layout.addWidget(date_lbl)
        layout.addWidget(desc_lbl)

        return group

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DashboardWindow()
    window.show()
    sys.exit(app.exec_())
