import sys
import os
import io
import requests
import qrcode

from PyQt5 import QtCore, QtGui, QtWidgets
from VetClinic.GUI.windows.Doctor.main_window import MainWindow

API_LOGIN_URL = "http://127.0.0.1:8000/users/login"
API_CONFIRM_TOTP_URL = "http://127.0.0.1:8000/users/confirm-totp"

def round_pixmap(pixmap, radius):
    """Przetwarza pixmapę, nadając jej zaokrąglone rogi o zadanym promieniu."""
    if pixmap.isNull():
        return pixmap
    rounded = QtGui.QPixmap(pixmap.size())
    rounded.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(rounded)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    path = QtGui.QPainterPath()
    rect = QtCore.QRectF(pixmap.rect())
    path.addRoundedRect(rect, radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    return rounded

class SetupTOTPDialog(QtWidgets.QDialog):
    """
    Dialog do konfiguracji TOTP.
    Wyświetla QR Code oraz pole do wpisania 6-cyfrowego kodu.
    """
    def __init__(self, totp_uri, email, parent=None):
        super().__init__(parent)
        self.totp_uri = totp_uri
        self.email = email
        self.setWindowTitle("Konfiguracja TOTP")
        self.resize(350, 450)
        
        # Nadanie nazwy obiektowi, by móc go selektywnie stylizować
        self.setObjectName("SetupTOTPDialog")
        
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        info_label = QtWidgets.QLabel(
            "Zeskanuj poniższy kod QR w Google Authenticator,\n"
            "a następnie wpisz wygenerowany 6-cyfrowy kod:"
        )
        layout.addWidget(info_label)
        info_label.setObjectName("info_label") 

        self.qr_label = QtWidgets.QLabel()
        layout.addWidget(self.qr_label)
        self.generate_qr(self.totp_uri)

        self.totp_input = QtWidgets.QLineEdit()
        self.totp_input.setPlaceholderText("Wpisz 6-cyfrowy kod TOTP")
        self.totp_input.setMaxLength(6)
        layout.addWidget(self.totp_input)

        self.confirm_button = QtWidgets.QPushButton("Potwierdź TOTP")
        self.confirm_button.clicked.connect(self.confirm_totp)
        layout.addWidget(self.confirm_button)

        self.status_label = QtWidgets.QLabel("")
        layout.addWidget(self.status_label)
        
        # Przykładowa stylizacja QSS
        self.setStyleSheet("""
            #SetupTOTPDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                font-family: Arial, sans-serif;
                font-size: 12pt;
                color: #333;
            }
            QLineEdit {
                border: 1px solid #aaa;
                border-radius: 4px;
                padding: 5px;
                font-size: 11pt;
            }
            QPushButton {
                background-color: #2d89ef;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #1b5fbd;
            }
            #SetupTOTPDialog QLineEdit:hover {
                border: 1px solid #66afe9;
            }
            #info_label{
                font-size: 10pt;
                color: #555;
                font-family: arial, sans-serif;
            }
        """)

    def generate_qr(self, totp_uri):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qimg = QtGui.QImage()
        qimg.loadFromData(buf.getvalue(), "PNG")
        pixmap = QtGui.QPixmap.fromImage(qimg)
        self.qr_label.setPixmap(pixmap)
        self.qr_label.setScaledContents(True)

    def confirm_totp(self):
        totp_code = self.totp_input.text().strip()
        if not totp_code:
            QtWidgets.QMessageBox.warning(self, "Błąd", "Wprowadź kod TOTP!")
            return
        payload = {"email": self.email, "totp_code": totp_code}
        try:
            response = requests.post(API_CONFIRM_TOTP_URL, json=payload)
            if response.status_code == 200:
                QtWidgets.QMessageBox.information(self, "Sukces", "TOTP skonfigurowany pomyślnie!")
                self.accept()
            else:
                detail = response.json().get("detail", "Błąd potwierdzenia TOTP")
                QtWidgets.QMessageBox.warning(self, "Błąd", f"Nie udało się potwierdzić TOTP")
                self.status_label.setText("Błąd potwierdzenia TOTP.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Błąd", f"Problem z połączeniem: {e}")
            self.status_label.setText("Błąd połączenia z API.")

class ProportionalImageLabel(QtWidgets.QLabel):
    """QLabel, która automatycznie przeskalowuje pixmapę zachowując proporcje, a jej sizeHint odzwierciedla te proporcje."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self._aspect_ratio = None  # przechowuje stosunek szerokości do wysokości
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def setPixmap(self, pixmap):
        # Zaokrąglamy obrazek przy użyciu round_pixmap (promień 20 pikseli)
        rounded = round_pixmap(pixmap, 45 )
        self._pixmap = rounded
        if self._pixmap and not self._pixmap.isNull():
            self._aspect_ratio = self._pixmap.width() / self._pixmap.height()
        else:
            self._aspect_ratio = None
        self.updateScaledPixmap()
        self.updateGeometry()

    def updateScaledPixmap(self):
        if self._pixmap and not self._pixmap.isNull():
            # Używamy aktualnego rozmiaru widgetu, ale musimy go zabezpieczyć przed zerową szerokością lub wysokością
            current_size = self.size()
            if current_size.width() > 0 and current_size.height() > 0:
                scaled = self._pixmap.scaled(current_size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                super().setPixmap(scaled)
        else:
            super().setPixmap(self._pixmap)

    def resizeEvent(self, event):
        self.updateScaledPixmap()
        super().resizeEvent(event)

    def sizeHint(self):
        if self._aspect_ratio is not None:
            # Preferowany rozmiar: bieżąca szerokość, a wysokość na podstawie proporcji
            return QtCore.QSize(self.width(), int(self.width() / self._aspect_ratio))
        else:
            return super().sizeHint()

class LoginWindow(QtWidgets.QWidget):
    """
    Okno logowania z layoutem dwukolumnowym:
      - Po lewej stronie formularz wzorowany na przedstawionym designie (tytuł, pola, checkbox, linki, przycisk).
      - Po prawej ilustracja.
    Jeśli TOTP jest wymagane (status 400 z "TOTP code required" lub status 201),
    wyświetla pole do wpisania kodu TOTP lub okno dialogowe do konfiguracji.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VetClinic - Logowanie")
        self.setFixedSize(1000, 650)  
        self.init_ui()

    def init_ui(self):
        # Główny layout horyzontalny z marginesami
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(40, 15, 15, 15)

        # ========== LEWA CZĘŚĆ: FORMULARZ ==========
        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Nagłówek z łamaniem linii
        label_title = QtWidgets.QLabel("Cześć!\nWitaj ponownie")
        font_title = QtGui.QFont("Arial", 22, QtGui.QFont.Bold)
        label_title.setFont(font_title)
        
        label_subtitle = QtWidgets.QLabel("Witamy w VetClinic!")
        font_subtitle = QtGui.QFont("Arial", 12)
        label_subtitle.setFont(font_subtitle)
        label_subtitle.setStyleSheet("color: #666;")
        
        self.email_input = QtWidgets.QLineEdit()
        self.email_input.setPlaceholderText("przykładowy@przykład.pl")

        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Hasło")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        
        self.login_button = QtWidgets.QPushButton("Zaloguj")
        self.login_button.setObjectName("loginButton")
        self.login_button.setFixedHeight(40)
        self.login_button.clicked.connect(self.handle_login)

        # Dodaj pola do wpisania TOTP, domyślnie ukryte:
        self.totp_input = QtWidgets.QLineEdit()
        self.totp_input.setPlaceholderText("Wprowadź 6-cyfrowy kod TOTP")
        self.totp_input.setMaxLength(6)
        self.totp_input.setVisible(False)
        
        # Dodajemy elementy do lewej części
        left_layout.addStretch(1)
        left_layout.addWidget(label_title)
        left_layout.addWidget(label_subtitle)
        left_layout.addSpacing(20)
        left_layout.addWidget(self.email_input)
        left_layout.addWidget(self.password_input)
        left_layout.addWidget(self.totp_input)
        left_layout.addSpacing(20)
        left_layout.addWidget(self.login_button)
        left_layout.addStretch(2)
        
        # ========== PRAWA CZĘŚĆ: OBRAZ ==========
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addStretch(1)
        
        self.image_label = ProportionalImageLabel()
        self.image_label.setMinimumWidth(1024)
        self.image_label.setMinimumSize(450, 400)
        
        current_dir = os.path.dirname(os.path.abspath(__file__)) 
        image_path = os.path.join(current_dir, "..", "Resources", "Login_picture.png")
        pixmap = QtGui.QPixmap(image_path)
        if pixmap.isNull():
            print("Nie udało się załadować obrazu z:", image_path)
        else:
            self.image_label.setPixmap(pixmap)
        
        # Dodajemy obraz do prawego layoutu
        right_layout.addWidget(self.image_label, alignment=QtCore.Qt.AlignCenter)
        right_layout.addStretch(1)
        
        # Dodajemy oba widgety do głównego layoutu – lewa i prawa część
        main_layout.addWidget(left_widget, stretch=1)
        main_layout.addWidget(right_widget, stretch=1)
        self.setLayout(main_layout)
        
        # Stylizacja QSS – jednolite tło i zaokrąglone rogi dla obrazka
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
            }
            #loginButton {
                background-color: #2d89ef;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 15px;
            }
            #loginButton:hover {
                background-color: #1b5fbd;
            }
            QLabel {
                font-family: Arial, sans-serif;
            }
            /* Zaokrąglamy rogi obrazu na etykiecie */
            QLabel:hasPixmap {
                border-radius: 20px;
                overflow: hidden;
                border: 2px solid #ccc;
            }
        """)

    # ========= OBSŁUGA LOGOWANIA =========
    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        totp_code = self.totp_input.text().strip() if self.totp_input.isVisible() else None

        if not email or not password:
            QtWidgets.QMessageBox.warning(self, "Błąd", "Podaj adres email i hasło.")
            return

        payload = {"email": email, "password": password}
        if totp_code:
            payload["totp_code"] = totp_code

        try:
            response = requests.post(API_LOGIN_URL, json=payload)
            if response.status_code == 200:
                # Logowanie udane
                data = response.json()
                user_role = data.get("role", "nieznana")
                self.hide()
                self.main_window = MainWindow(user_role)
                self.main_window.show()
            elif response.status_code == 201:
                # Pierwsze logowanie – konfiguracja TOTP
                data = response.json()
                totp_uri = data.get("totp_uri")
                if totp_uri:
                    dialog = SetupTOTPDialog(totp_uri, email, self)
                    dialog.exec_()
                    # Po konfiguracji TOTP, ujawniamy pole do wpisania kodu
                    self.totp_input.setVisible(True)
                else:
                    QtWidgets.QMessageBox.warning(self, "Błąd", "Brak provisioning URI od API.")
            elif response.status_code == 400 and "TOTP code required" in response.json().get("detail", ""):
                # API informuje, że trzeba podać kod TOTP
                self.totp_input.setVisible(True)
            else:
                detail = response.json().get("detail", "Błąd logowania")
                QtWidgets.QMessageBox.warning(self, "Błąd", f"Logowanie nie powiodło się: {detail}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Błąd", f"Nie udało się połączyć z API: {e}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
