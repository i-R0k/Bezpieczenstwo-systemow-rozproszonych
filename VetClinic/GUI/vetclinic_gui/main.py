import sys
from PyQt5.QtWidgets import QApplication, QInputDialog, QMessageBox
from vetclinic_gui.windows.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    # 1) Wybór roli
    roles = ["Administrator","Recepcjonista","Lekarz","Klient"]
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
    role_map = {"Lekarz": "doctor", "Recepcjonista": "receptionist", "Administrator": "admin", "klient": "client"}
    user_role = role_map[role_name]

    # 2) Jeżeli to doktor – poproś o ID
    doctor_id = None
    if user_role == "doctor":
        doctor_id, ok = QInputDialog.getInt(
            None,
            "ID lekarza",
            "Podaj identyfikator lekarza (liczba całkowita):",
            value=1,   # domyślna wartość
            min=1,     # minimalna
            max=9999,  # dowolne
            step=1
        )
        if not ok:
            QMessageBox.information(None, "Koniec", "Nie podano ID lekarza. Kończę.")
            sys.exit(0)

    # 3) Uruchom główne okno, przekazując user_role i doctor_id
    window = MainWindow(user_role=user_role, doctor_id=doctor_id)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
