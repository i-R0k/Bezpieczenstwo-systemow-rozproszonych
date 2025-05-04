# main.py
import sys
from PyQt5.QtWidgets import QApplication, QInputDialog, QMessageBox
from windows.Doctor.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    # 1) Pytamy o rolę
    roles = ["Doktor", "Recepcjonista", "Admin"]
    role_name, ok = QInputDialog.getItem(
        None,
        "Wybór grupy użytkownika",
        "Zaloguj się jako:",
        roles,
        0,
        False
    )
    if not ok:
        QMessageBox.information(None, "Koniec", "Nie wybrano roli. Kończę.")
        sys.exit(0)

    # 2) Mapowanie na wewnętrzny klucz
    role_map = {
        "Doktor": "doctor",
        "Recepcjonista": "receptionist",
        "Admin": "admin"
    }
    user_role = role_map.get(role_name, "doctor")

    # 3) Startujemy główne okno z rolą
    window = MainWindow(user_role=user_role)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
