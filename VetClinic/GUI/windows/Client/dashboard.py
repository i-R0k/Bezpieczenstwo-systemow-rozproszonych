import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QGroupBox,
    QLabel, QPushButton, QLineEdit, QFrame,
    QTableWidget, QTableWidgetItem,
    QCalendarWidget, QToolButton, QHeaderView,
    QSizePolicy, QSplitter, QToolTip
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QPainter, QBrush, QColor, QCursor, QPen
from PyQt5.QtChart import (
    QChart, QChartView,
    QLineSeries, QSplineSeries, QAreaSeries,
    QScatterSeries, QCategoryAxis, QValueAxis
)

from VetClinic.GUI.Widgets.smooth_chart_view import SmoothChartView

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

        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

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
   
    def _create_sidebar(self) -> QFrame:
        frame = QFrame()
        frame.setFixedWidth(260)
        frame.setStyleSheet("background-color:#2f3b52;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        logo = QLabel("<span style='font-size:24px; font-weight:bold; color:#ffffff;'>Vet<span style='color:#38a2db;'>Clinic</span></span>")
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)
        for name in ["Główna", "Aktualności", "Dashboard", "Usługi i cennik", "Lekarze", "Kontakt", "Ustawienia konta", "Wyloguj"]:
            btn = QPushButton(name)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFlat(True)
            btn.setStyleSheet(
                "QPushButton { text-align:left; padding:8px; color:#ffffff; font-size:16px; }"
                "QPushButton:hover { background-color: #2e3a50; }"
            )
            if name == "Dashboard":
                btn.setStyleSheet(
                    "QPushButton { text-align:left; padding:8px; background-color:#38a2db; color:#fff; font-size:16px; border-radius:5px; }"
                    "QPushButton:hover { background-color:#2e97c9; }"
                )
            layout.addWidget(btn)
        layout.addStretch()
        user_lbl = QLabel("<span style='color:#ffffff;'>Cześć, <b>Anna</b></span>")
        user_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(user_lbl)
        return frame

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
        # ——— Kontener z białym tłem i ramką jak w Vaccinations ———
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

        # ——— Layout i nagłówek ———
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

        # ——— Tabela ———
        table = QTableWidget(4, 4)
        table.setHorizontalHeaderLabels(["Rozpoznanie", "Leczenie", "Data kontroli", ""])

        # wyłącz edycję, zaznaczanie, focus, włącz zawijanie
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)
        table.setWordWrap(True)

        # usuń obramowanie tabeli, grid i numerację wierszy
        table.setFrameShape(QFrame.NoFrame)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)

        # rozkład kolumn: auto, stretch, auto, fixed
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        table.setColumnWidth(3, 20)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # style tabeli (nagłówki i wiersze) jak w Vaccinations
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
            QTableView::item {
                border-bottom: 1px solid #e5e7eb;
                padding: 10px 6px;
            }
        """)

        # ——— 5) Delikatny, 8px scrollbar ———
        vsb = table.verticalScrollBar()
        vsb.setStyleSheet("""
            /* Główny tor (track) */
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            /* Rączka (handle) */
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.15);
                border-radius: 4px;
                min-height: 30px;
            }
            /* Usuń przyciski góra/dół */
            QScrollBar::sub-line, QScrollBar::add-line {
                height: 0px;
            }
            /* Reszta (puste miejsca) */
            QScrollBar::add-page, QScrollBar::sub-page {
                background: transparent;
            }
        """)

        # ——— Wypełnienie danymi ———
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
        # ——— 1) Grupa z białym tłem i ramką jak w karcie medycznej ———
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

        # ——— 2) Layout i nagłówek jak w medycznej ———
        layout = QVBoxLayout(group)
        # korzystamy z domyślnych contentsMargins QGroupBox, 
        # żeby zachować ten sam padding co w medycznej

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

        # ——— 3) Tabela bez gridu, z liniami oddzielającymi wiersze ———
        table = QTableWidget(6, 5)
        table.setHorizontalHeaderLabels([
            "Choroba", "Status", "Szczepionka", "Pierwotne", "Powtórka"
        ])

        # wyłącz edycję, zaznaczanie, focus, włącz zawijanie
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)
        table.setWordWrap(True)

        # usuń domyślną siatkę i numerację wierszy
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)

        # rozciągnięcie kolumn analogicznie do karty medycznej
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # ——— 4) Style tabeli ———
        table.setStyleSheet("""
            /* cała tabela bez własnej ramki */
            QTableWidget {
                border: none;
                background-color: transparent;
            }
            /* nagłówki z białym tłem i dolnym border */
            QHeaderView::section {
                background-color: #ffffff;
                border: none;
                padding: 8px;
                font-weight: 600;
                color: #111827;
                border-bottom: 2px solid #e5e7eb;
            }
            /* wiersze – tylko dolna linia i padding */
            QTableView::item {
                border-bottom: 1px solid #e5e7eb;
                padding: 10px 6px;
            }
        """)

        # ——— 5) Delikatny, 8px scrollbar ———
        vsb = table.verticalScrollBar()
        vsb.setStyleSheet("""
            /* Główny tor (track) */
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            /* Rączka (handle) */
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.15);
                border-radius: 4px;
                min-height: 30px;
            }
            /* Usuń przyciski góra/dół */
            QScrollBar::sub-line, QScrollBar::add-line {
                height: 0px;
            }
            /* Reszta (puste miejsca) */
            QScrollBar::add-page, QScrollBar::sub-page {
                background: transparent;
            }
        """)

        # ——— 5) Dane przykładowe ———
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

    def _create_weight_chart(self) -> QGroupBox:
        # ——— 1) Kontener z ramką i białym tłem, identyczny jak w pozostałych sekcjach ———
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

        # ——— 2) Layout i nagłówek sekcji ———
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

        # ——— 3) Dane i ich marginesy ———
        weights = [2000,2500,2300,2400,2600,2800,3000,3200,3100,3000,2900,2800]
        months  = ["Sty","Lut","Mar","Kwi","Maj","Cze","Lip","Sie","Wrz","Paź","Lis","Gru"]

        mn, mx = min(weights), max(weights)
        dy = (mx - mn) * 0.1
        y_min, y_max = mn - dy, mx + dy

        # ——— 4) SplineSeries (gładka linia) ———
        spline   = QSplineSeries()
        baseline = QSplineSeries()
        for i, w in enumerate(weights, 1):
            spline.append(i, w)
            baseline.append(i, y_min)

        pen = QPen(QColor("#38A2DB"))
        pen.setWidth(2)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        spline.setPen(pen)

        # ——— 5) Punkty i tooltip ———
        scatter = QScatterSeries()
        scatter.setMarkerSize(8)
        scatter.setColor(QColor("#38A2DB"))
        scatter.setBorderColor(QColor("#ffffff"))
        for i, w in enumerate(weights, 1):
            scatter.append(i, w)
     
        def show_tt(pt, state):
            if state:
                m = months[int(pt.x())-1]
                QToolTip.showText(QCursor.pos(), f"{m} {int(pt.y())} g")
        scatter.hovered.connect(show_tt)
     
        # ——— 6) Tworzenie wykresu i osi ———
        chart = QChart()
        chart.addSeries(spline)
        chart.addSeries(scatter)
        chart.setBackgroundVisible(False)
        chart.legend().hide()
     
        axisX = QCategoryAxis()
        for i, m in enumerate(months, 1):
            axisX.append(m, i)
        axisX.setRange(1, len(months) + 0.1 * len(months))
        chart.addAxis(axisX, Qt.AlignBottom)
        spline.attachAxis(axisX)
        scatter.attachAxis(axisX)
     
        axisY = QValueAxis()
        axisY.setRange(y_min, y_max)
        axisY.setLabelFormat("%.0f")
        chart.addAxis(axisY, Qt.AlignLeft)
        spline.attachAxis(axisY)
        scatter.attachAxis(axisY)
     
        # ——— 7) Używamy SmoothChartView, który sam narysuje fill pod spline’em ———
        view = SmoothChartView(chart, spline, y_min)
        layout.addWidget(view)
     
        # ——— 8) Przechowujemy referencje, by obiekty nie zostały usunięte przez GC ———
        group._chart   = chart
        group._spline  = spline
        group._scatter = scatter
        group._axisX   = axisX
        group._axisY   = axisY
        group._view    = view
     
        return group

    def _create_clinic_visits(self) -> QGroupBox:
        # ——— 1) Kontener z ramką i białym tłem ———
        group = QGroupBox()
        group.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 16px;
            }
        """)

        # ——— 2) Nagłówek sekcji ———
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

        # ——— 3) Kalendarz ———
        cal = QCalendarWidget()
        cal.setFirstDayOfWeek(Qt.Monday)
        cal.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        cal.setHorizontalHeaderFormat(QCalendarWidget.ShortDayNames)
        cal.setNavigationBarVisible(True)
        cal.setGridVisible(False)
        cal.setStyleSheet("""
            /* cała powierzchnia kalendarza */
            QCalendarWidget {
                background-color: transparent;
                border: none;
            }
            /* nagłówek miesiąca + przyciski */
            QCalendarWidget QToolButton {
                margin: 4px;
                color: #111827;
                font-size: 14px;
                font-weight: bold;
            }
            /* tytuł (miesiąc + rok) */
            QCalendarWidget QSpinBox {
                width: 100px;
                font-size: 14px;
                font-weight: bold;
                color: #111827;
                background: transparent;
                border: none;
            }
            /* ukryj przyciski spinboxa */
            QCalendarWidget QSpinBox::up-button,
            QCalendarWidget QSpinBox::down-button {
                width: 0; height: 0;
            }
            /* widok dni */
            QCalendarWidget QAbstractItemView {
                selection-background-color: #38a2db;
                selection-color: white;
                outline: none;
                font-size: 12px;
            }
            /* pojedyncze dni */
            QCalendarWidget QAbstractItemView::item {
                border-radius: 4px;
                height: 28px;
                width: 28px;
                margin: 2px;
            }
            /* hover nad dniem */
            QCalendarWidget QAbstractItemView::item:hover {
                background: rgba(56,162,219,0.1);
            }
            /* zaznaczony dzień */
            QCalendarWidget QAbstractItemView::item:selected {
                background: #38a2db;
                color: white;
            }
        """)
        layout.addWidget(cal)

        # ——— 4) Informacja tekstowa ———
        date_lbl = QLabel("18.11.2020, 16:30")
        date_lbl.setStyleSheet(
            "color: #38a2db;"           # akcentowy niebieski
            "font-weight: bold;"
            "font-size: 14px;"
            "padding-left: 8px;"
        )
        # Opis wizyty w lekkim odcieniu szarości
        desc_lbl = QLabel("Kontrola i szczepienie, Dr. Petrikov V.V., pok.206")
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(
            "color: #4b5563;"           # ciemniejsza szarość
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