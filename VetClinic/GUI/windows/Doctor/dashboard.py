import sys

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, 
    QGroupBox, QLabel, QPushButton, QLineEdit, 
    QFrame, QTableWidget, QTableWidgetItem,
    QToolButton, QHeaderView, QSizePolicy, 
    QToolTip
)
from PyQt5.QtCore import Qt, QDate, QDateTime
from PyQt5.QtGui import (
    QFont, QPainter, QBrush, QColor,
    QCursor, QPen, QLinearGradient, QGradient
)
from PyQt5.QtChart import (
    QChart, QChartView, QLineSeries,
    QScatterSeries, QAreaSeries,
    QDateTimeAxis, QValueAxis
)

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        # główny layout strony (tylko content, bez sidebaru)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- górny pasek ---
        top_bar = self._create_top_bar()
        layout.addLayout(top_bar)

        # --- wiersz 1: nadchodzące + poprzednie wizyty ---
        row1 = QHBoxLayout()
        row1.setSpacing(15)
        upcoming = self._create_upcoming_visits()
        previous = self._create_previous_visits()
        for w in (upcoming, previous):
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            w.setMinimumWidth(0)
        row1.addWidget(upcoming, 1)
        row1.addWidget(previous, 1)
        layout.addLayout(row1, 3)

        # --- wiersz 2: statystyki wizyt ---
        row2 = QHBoxLayout()
        stats = self._create_appointments_stats()
        stats.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        row2.addWidget(stats)
        layout.addLayout(row2, 2)

    def _create_sidebar(self) -> QFrame:
        frame = QFrame()
        frame.setFixedWidth(260)
        frame.setStyleSheet("background-color:#2f3b52;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        logo = QLabel("<span style='font-size:24px; font-weight:bold; color:#ffffff;'>"
                      "Vet<span style='color:#38a2db;'>Clinic</span></span>")
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        for name in ["Dashboard", "Pacjenci", "Wizyty", "Analizy", "Ustawienia", "Wyloguj"]:
            btn = QPushButton(name)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFlat(True)
            btn.setStyleSheet(
                "QPushButton { text-align:left; padding:8px; color:#ffffff; font-size:16px; }"
                "QPushButton:hover { background-color: #2e3a50; }"
            )
            layout.addWidget(btn)

        layout.addStretch()
        user_lbl = QLabel("<span style='color:#ffffff;'>Dr <b>Anna Kowalska</b></span>")
        user_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(user_lbl)
        return frame

    def _create_top_bar(self):
        layout = QHBoxLayout()
        search = QLineEdit()
        search.setPlaceholderText("Szukaj pacjenta...")
        search.setFixedHeight(30)
        search.setStyleSheet(
            "QLineEdit { border:1px solid #d1d5db; border-radius:15px; padding-left:10px; }"
        )
        layout.addWidget(search)
        layout.addStretch()
        logout = QPushButton("Wyloguj")
        logout.setCursor(Qt.PointingHandCursor)
        logout.setStyleSheet(
            "QPushButton { padding:8px 16px; background-color:#f87171; color:#fff; border:none; border-radius:15px; }"
            "QPushButton:hover { background-color:#ef4444; }"
        )
        layout.addWidget(logout)
        return layout
   
    def _create_upcoming_visits(self) -> QGroupBox:
        group = QGroupBox()
        group.setStyleSheet(self._groupbox_css())

        layout = QVBoxLayout(group)

        header = QHBoxLayout()
        title = QLabel("Nadchodzące wizyty")
        title.setFont(QFont('Arial', 12, QFont.Bold))
        header.addWidget(title)
        header.addStretch()
        menu_btn = QToolButton()
        menu_btn.setText("\u22EE")
        menu_btn.setStyleSheet(
            "QToolButton { border: none; font-size: 16px; color: #6b7280; }"
            "QToolButton:hover { color: #111827; }"
        )
        header.addWidget(menu_btn)
        layout.addLayout(header)

        table = QTableWidget(5, 4)
        table.setHorizontalHeaderLabels(["Data", "Pacjent", "Godzina", "Powód wizyty"])

        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)

        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)

        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        table.setWordWrap(True)

        table.setStyleSheet("""
            QTableWidget { border: none; background-color: transparent; }
            QHeaderView::section {
                background-color: #ffffff; border: none; padding:8px;
                font-weight:600; color:#111827; border-bottom:2px solid #e5e7eb;
            }
            QTableView::item { border-bottom:1px solid #e5e7eb; padding:10px 6px; }
        """)


        data = [
            ("20.04.2025", "Burek",   "09:30", "Kontrola szczepienia"),
            ("20.04.2025", "Mruczek", "10:00", "Zabieg usunięcia kleszcza"),
            ("21.04.2025", "Łatek",   "11:15", "Badanie krwi"),
            ("22.04.2025", "Reksio",  "08:45", "Szczepienie podstawowe"),
            ("22.04.2025", "Denis",   "14:00", "Konsultacja dermatologiczna"),
        ]
        for r, (d, p, h, reason) in enumerate(data):
            table.setItem(r, 0, QTableWidgetItem(d))


            item_p = QTableWidgetItem(p)
            item_p.setTextAlignment(Qt.AlignCenter)
            table.setItem(r, 1, item_p)

            table.setItem(r, 2, QTableWidgetItem(h))
            table.setItem(r, 3, QTableWidgetItem(reason))

        layout.addWidget(table)
        return group

    def _create_previous_visits(self) -> QGroupBox:
        group = QGroupBox()
        group.setStyleSheet(self._groupbox_css())

        layout = QVBoxLayout(group)

        header = QHBoxLayout()
        title = QLabel("Poprzednie wizyty")
        title.setFont(QFont('Arial', 12, QFont.Bold))
        header.addWidget(title)
        header.addStretch()
        menu_btn = QToolButton()
        menu_btn.setText("\u22EE")
        menu_btn.setStyleSheet(
            "QToolButton { border: none; font-size: 16px; color: #6b7280; }"
            "QToolButton:hover { color: #111827; }"
        )
        header.addWidget(menu_btn)
        layout.addLayout(header)

        table = QTableWidget(5, 4)
        table.setHorizontalHeaderLabels(["Data", "Pacjent", "Status", "Powód wizyty"])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.setWordWrap(True)
        table.setStyleSheet("""
            QTableWidget { border: none; background-color: transparent; }
            QHeaderView::section {
                background-color: #ffffff; border: none; padding:8px;
                font-weight:600; color:#111827; border-bottom:2px solid #e5e7eb;
            }
            QTableView::item { border-bottom:1px solid #e5e7eb; padding:10px 6px; }
        """)

        data = [
            ("15.04.2025", "Burek",   "odbyta",    "Kontrola pooperacyjna"),
            ("14.04.2025", "Puszek",  "anulowana",  "Brak powodu podanego"),
            ("13.04.2025", "Mruczek", "odbyta",    "Wyniki badań krwi"),
            ("12.04.2025", "Łatek",   "odbyta",    "Szczepienie przypominające"),
            ("10.04.2025", "Reksio",  "anulowana",  "Objawy alergii skórnej"),
        ]
        for r, (d, p, s, reason) in enumerate(data):
            table.setItem(r, 0, QTableWidgetItem(d))

            item_p = QTableWidgetItem(p)
            item_p.setTextAlignment(Qt.AlignCenter)
            table.setItem(r, 1, item_p)

            st = QTableWidgetItem(s)
            st.setForeground(QBrush(QColor("#10B981")) if s == "odbyta" else QBrush(QColor("#EF4444")))
            table.setItem(r, 2, st)

            table.setItem(r, 3, QTableWidgetItem(reason))

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

    def _create_appointments_stats(self) -> QGroupBox:
        group = QGroupBox()
        group.setStyleSheet(self._groupbox_css())
        layout = QVBoxLayout(group)

        header = QHBoxLayout()
        title = QLabel("Statystyki wizyt")
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

        date_values = [
            (QDate(2025,4,15),  4),
            (QDate(2025,4,16),  7),
            (QDate(2025,4,17),  5),
            (QDate(2025,4,18), 10),
            (QDate(2025,4,19), 12),
            (QDate(2025,4,20),  8),
            (QDate(2025,4,21),  6),
            (QDate(2025,4,22), 11),
            (QDate(2025,4,23),  9),
            (QDate(2025,4,24), 13),
        ]

        raw_pts = [
            (QDateTime(d).toMSecsSinceEpoch(), v)
            for d, v in date_values
        ]

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
                p0 = pts[i-1] if i-1 >= 0   else pts[i]
                p1 = pts[i]
                p2 = pts[i+1]
                p3 = pts[i+2] if i+2 < n    else pts[i+1]
                for s in range(samples):
                    t = s / samples
                    dense.append(CR(p0,p1,p2,p3,t))
            dense.append(pts[-1])
            return dense

        dense_pts = catmull_rom(raw_pts, samples=20)

        top = QLineSeries()
        for x, y in dense_pts:
            top.append(x, y)
        pen = QPen(QColor("#38A2DB"))
        pen.setWidth(2); pen.setCapStyle(Qt.RoundCap); pen.setJoinStyle(Qt.RoundJoin)
        top.setPen(pen)

        base = QLineSeries()
        for x, _ in dense_pts:
            base.append(x, 0)

        area = QAreaSeries(top, base)
        grad = QLinearGradient(0, 0, 0, 1)
        grad.setCoordinateMode(QGradient.ObjectBoundingMode)
        grad.setColorAt(0.0, QColor(56,162,219,120))
        grad.setColorAt(1.0, QColor(56,162,219,20))
        area.setBrush(QBrush(grad))
        area.setPen(QPen(Qt.NoPen))

        scatter = QScatterSeries()
        scatter.setMarkerSize(8)
        scatter.setColor(QColor("#38A2DB"))
        scatter.setBorderColor(QColor("#ffffff"))
        for d, v in date_values:
            ms = QDateTime(d).toMSecsSinceEpoch()
            scatter.append(ms, v)
        def show_tt(pt, state):
            if state:
                dt = QDateTime.fromMSecsSinceEpoch(int(pt.x())).date().toString("dd.MM.yyyy")
                QToolTip.showText(QCursor.pos(), f"{dt}: {int(pt.y())} wizyt")
        scatter.hovered.connect(show_tt)

        chart = QChart()
        chart.addSeries(area)
        chart.addSeries(top)
        chart.addSeries(scatter)
        chart.setBackgroundVisible(False)
        chart.legend().hide()

        axisX = QDateTimeAxis()
        axisX.setFormat("dd.MM.yyyy")
        axisX.setTickCount(len(date_values))
        axisX.setRange(
            QDateTime(date_values[0][0]),
            QDateTime(date_values[-1][0])
        )
        chart.addAxis(axisX, Qt.AlignBottom)
        for s in (area, top, scatter):
            s.attachAxis(axisX)

        ymax = max(v for _,v in date_values) * 1.1
        axisY = QValueAxis()
        axisY.setRange(0, ymax)
        axisY.setLabelFormat("%d")
        chart.addAxis(axisY, Qt.AlignLeft)
        for s in (area, top, scatter):
            s.attachAxis(axisY)

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
