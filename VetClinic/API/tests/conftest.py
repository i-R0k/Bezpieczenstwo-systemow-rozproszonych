# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from vetclinic_api.main import app 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from vetclinic_api.core.database import Base, get_db

# Konfiguracja testowej bazy danych – tutaj używamy SQLite w pliku testowym,
# możesz też użyć bazy pamięciowej ("sqlite:///:memory:")
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

# Fixture tworzące schemat (tabele) w testowej bazie danych
@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    # Przed testami tworzymy schemat
    Base.metadata.create_all(bind=engine_test)
    yield
    # Po zakończeniu testów sprzątamy
    Base.metadata.drop_all(bind=engine_test)

# Fixture udostępniające instancję sesji bazodanowej
@pytest.fixture(scope="function")
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Nadpisujemy dependency get_db, aby podczas testów korzystać z naszej testowej sesji
@pytest.fixture(scope="function", autouse=True)
def override_get_db(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.pop(get_db, None)

# Fixture TestClient, dostępny jako 'client'
@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
