import pytest
from sqlalchemy import text
from src.app.database import engine, SessionLocal
from sqlalchemy.exc import OperationalError

def test_database_connection():
    """
    Testuje, czy uda się nawiązać połączenie z bazą danych
    i wykonać proste zapytanie SELECT 1.
    """
    try:
        connection = engine.connect()
        result = connection.execute(text("SELECT 1"))
        # Zakładamy, że zapytanie SELECT 1 zwróci wartość 1
        assert result.scalar() == 1
        connection.close()
    except OperationalError as e:
        pytest.fail(f"Nie udało się połączyć z bazą danych: {e}")

def test_session_creation():
    """
    Testuje, czy można utworzyć sesję (SessionLocal) i wykonać proste zapytanie.
    """
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1"))
        assert result.scalar() == 1
    finally:
        db.close()
