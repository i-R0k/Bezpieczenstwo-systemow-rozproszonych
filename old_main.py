from PyQt5 import QtCore, QtGui, QtWidgets

class MainWindow(QtWidgets.QWidget):
    """
    Główne okno aplikacji.
    Wyświetla rolę zalogowanego użytkownika, np. "Twoja rola: doktor".
    """
    def __init__(self, user_role, parent=None):
        super().__init__(parent)
        self.user_role = user_role
        self.setWindowTitle("VetClinic - Główne Okno")
        self.setFixedWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        role_label = QtWidgets.QLabel(f"Twoja rola: {self.user_role}")
        role_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(role_label)
        self.setLayout(layout)