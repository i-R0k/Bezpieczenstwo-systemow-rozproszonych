from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget,
    QFrame, QLabel
)
from .dashboard import DashboardPage
from .visit import VisitsWindow

class MainWindow(QMainWindow):
    def __init__(self, user_role: str, doctor_id: int = None):
        super().__init__()
        self.user_role = user_role
        self.doctor_id = doctor_id  # ID zalogowanego lekarza
        self.pages_map = {}
        self.setWindowTitle("VetClinic")
        self.setMinimumSize(1080, 720)
        self._setup_ui()
        self.showMaximized()

    def _setup_ui(self):
        container = QWidget()
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)

        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        self.pages = QStackedWidget()
        role_pages = {
            "doctor": [
                ("Dashboard", DashboardPage),
                ("Wizyty", VisitsWindow),
            ],
            "receptionist": [
                ("Wizyty", VisitsWindow),
            ],
        }

        for label, PageClass in role_pages.get(self.user_role, []):
            btn = QPushButton(label)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFlat(True)
            btn.setStyleSheet(
                "QPushButton { text-align:left; padding:8px; color:#ffffff; font-size:16px; }"
                "QPushButton:hover { background-color: #2e3a50; }"
            )
            btn.clicked.connect(lambda _, l=label: self._navigate_to(l))
            sidebar.layout().addWidget(btn)

            # Instantiate page, pass doctor_id to VisitsWindow
            if label == "Wizyty":
                page = PageClass(self.doctor_id)
            else:
                page = PageClass()
            idx = self.pages.count()
            self.pages.addWidget(page)
            self.pages_map[label] = idx

        sidebar.layout().addStretch()
        main_layout.addWidget(self.pages)
        self.setCentralWidget(container)

        if self.pages.count() > 0:
            self.pages.setCurrentIndex(0)

    def _create_sidebar(self) -> QFrame:
        frame = QFrame()
        frame.setFixedWidth(260)
        frame.setStyleSheet("background-color: #2f3b52;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        logo = QLabel(
            "<span style='font-size:24px; font-weight:bold; color:#ffffff;'>"
            "Vet<span style='color:#38a2db;'>Clinic</span></span>"
        )
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)
        return frame

    def _navigate_to(self, label: str):
        idx = self.pages_map.get(label)
        if idx is not None:
            self.pages.setCurrentIndex(idx)
