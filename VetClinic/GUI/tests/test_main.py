import pytest
from unittest.mock import patch, MagicMock
from PyQt5.QtWidgets import QApplication, QMessageBox
pytestmark = pytest.mark.gui

@pytest.fixture(scope="session")
def app():
    return QApplication([])

# ================= LOGIN WINDOW =================

@patch("vetclinic_gui.windows.login_window.requests.post")
@patch("vetclinic_gui.windows.login_window.MainWindow")
@patch("vetclinic_gui.windows.login_window.ChangePasswordDialog")
@patch("vetclinic_gui.windows.login_window.SetupTOTPDialog")
def test_loginwindow_login_all_branches(mock_totp, mock_chpwd, mock_main, mock_post, app):
    from vetclinic_gui.windows.login_window import LoginWindow

    win = LoginWindow()
    win.email_input.setText("test@x.pl")
    win.password_input.setText("haslo")

    # 1. Pierwsze logowanie - status 202 (wymagana zmiana hasła)
    resp202 = MagicMock(status_code=202)
    mock_post.return_value = resp202
    mock_chpwd.return_value.exec_.return_value = 0  # Cancel zmiany hasła
    win.handle_login()
    mock_chpwd.assert_called()
    mock_chpwd.return_value.exec_.return_value = 1  # Akceptacja zmiany hasła
    win.handle_login()

    # 2. Provisioning TOTP - status 201
    resp201 = MagicMock(status_code=201)
    resp201.json.return_value = {"totp_uri": "otpauth://..."}
    mock_post.return_value = resp201
    win.handle_login()
    mock_totp.assert_called()

    # 3. Logowanie OK - status 200 (wszystkie role)
    for role, key in [
        ("klient", "client_id"),
        ("lekarz", "doctor_id"),
        ("recepcjonista", "receptionist_id"),
        ("admin", "user_id"),
    ]:
        resp200 = MagicMock(status_code=200)
        resp200.json.return_value = {"role": role, "user_id": 11}
        mock_post.return_value = resp200
        win.handle_login()
        mock_main.assert_called()
        assert hasattr(win, "main_window")

    # 4. Wymuszony kod TOTP (status 400 z odpowiednim messagem)
    resp400 = MagicMock(status_code=400)
    resp400.json.return_value = {"detail": "Kod TOTP wymagany"}
    mock_post.return_value = resp400
    win.totp_input.setVisible(False)
    win.handle_login()
    win.show()   # <--- KLUCZOWE!
    assert win.totp_input.isVisible()

    # 5. Inny błąd (status 400 z message)
    resp400b = MagicMock(status_code=400)
    resp400b.json.return_value = {"detail": "Blad autoryzacji"}
    mock_post.return_value = resp400b
    with patch.object(QMessageBox, "warning") as warnmock:
        win.handle_login()
        assert warnmock.called

    # 6. Błąd API (wyjątek requests)
    mock_post.side_effect = Exception("serwer nie odpowiada")
    with patch.object(QMessageBox, "critical") as critmock:
        win.handle_login()
        assert critmock.called

def test_loginwindow_empty_fields(app):
    from vetclinic_gui.windows.login_window import LoginWindow
    win = LoginWindow()
    win.email_input.setText("")
    win.password_input.setText("")
    with patch.object(QMessageBox, "warning") as warnmock:
        win.handle_login()
        assert warnmock.called

# ============ RESET TOTP ==============

@patch("vetclinic_gui.windows.login_window.ResetTOTPDialog")
@patch("vetclinic_gui.windows.login_window.SetupTOTPDialog")
def test_loginwindow_handle_reset_totp(mock_totp, mock_reset, app):
    from vetclinic_gui.windows.login_window import LoginWindow
    win = LoginWindow()
    win.email_input.setText("xx@yy.pl")
    # symuluj Accept z nowym totp_uri
    mock_reset.return_value.exec_.return_value = 1
    mock_reset.return_value.totp_uri = "otpauth://xxx"
    win.handle_reset_totp()
    mock_totp.assert_called()
    # symuluj brak emaila
    win.email_input.setText("")
    with patch.object(QMessageBox, "warning") as warnmock:
        win.handle_reset_totp()
        assert warnmock.called
