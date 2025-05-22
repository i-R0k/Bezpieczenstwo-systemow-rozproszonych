from pathlib import Path
from dotenv import load_dotenv
import os

# znajdź katalog API (tam, gdzie leży .env)
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # .../VetClinic/API
DOTENV = BASE_DIR / ".env"
if not DOTENV.exists():
    raise FileNotFoundError(f"Nie znalazłem pliku .env pod {DOTENV}")
load_dotenv(DOTENV)

API_BASE_URL = "http://127.0.0.1:8000"

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

DB_FILENAME = "vetclinic.db"
DB_PATH = os.path.join(PROJECT_ROOT, DB_FILENAME)

DATABASE_URL = f"sqlite:///{DB_PATH}"

# Możesz dodać tutaj inne ustawienia, np. secret key, port serwera itp.
SECRET_KEY = os.getenv("SECRET_KEY", "twoj_sekret")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_FROM = os.getenv("SMTP_FROM")
