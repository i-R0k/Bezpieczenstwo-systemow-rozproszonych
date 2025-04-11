"""
Plik konfiguracyjny projektu.
"""

import os

# Przykładowa konfiguracja dla SQLite (na etapie developmentu)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Możesz dodać tutaj inne ustawienia, np. secret key, port serwera itp.
SECRET_KEY = os.getenv("SECRET_KEY", "twoj_sekret")
