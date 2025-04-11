"""
Konfiguracja SQLAlchemy: tworzymy silnik, sesję oraz deklarujemy bazę modeli.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import DATABASE_URL

# Utworzenie silnika połączenia do bazy danych
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Tworzymy sesję lokalną, która będzie wykorzystywana do komunikacji z bazą
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Deklaratywna baza modeli – wszystkie modele będą dziedziczyć po Base
Base = declarative_base()

def get_db():
    """Funkcja zależności, która tworzy sesję bazy danych i ją zamyka po wykorzystaniu."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
