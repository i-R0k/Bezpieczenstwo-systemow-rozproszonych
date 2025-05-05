import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

DB_FILENAME = "vetclinic.db"
DB_PATH = os.path.join(PROJECT_ROOT, DB_FILENAME)

DATABASE_URL = f"sqlite:///{DB_PATH}"

# Możesz dodać tutaj inne ustawienia, np. secret key, port serwera itp.
SECRET_KEY = os.getenv("SECRET_KEY", "twoj_sekret")
