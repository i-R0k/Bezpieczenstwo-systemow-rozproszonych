# System Zarządzania Kliniką Weterynaryjną

Projekt oparty na FastAPI, SQLAlchemy oraz zasadach defensywnego programowania. Celem projektu jest stworzenie aplikacji umożliwiającej kompleksowe zarządzanie kliniką weterynaryjną, obejmującej rejestrację użytkowników, zarządzanie wizytami, historię leczenia, dane zwierząt oraz obsługę faktur.

## Spis Treści

- [Opis Projektu](#opis-projektu)
- [Struktura Projektu](#struktura-projektu)
- [Instalacja i Uruchomienie](#instalacja-i-uruchomienie)
- [Testy](#testy)
- [Technologie](#technologie)

## Opis Projektu

Projekt został zaprojektowany zgodnie z najlepszymi praktykami defensywnego programowania. Kluczowe funkcjonalności systemu obejmują:
- **CRUD dla użytkowników** – rejestracja, logowanie oraz zarządzanie danymi użytkowników.
- **Zarządzanie wizytami** – planowanie i monitorowanie wizyt w klinice.
- **Historia leczenia** – rejestracja diagnoz, przebieg leczenia oraz notatek medycznych.
- **Zarządzanie danymi zwierząt** – informacje o zwierzętach, przypisanie do właścicieli.
- **Obsługa faktur** – generowanie i przetwarzanie płatności związanych z wizytami.

## Struktura projektu

```
Programowanie-Defensywne/
app/
├── __init__.py              # Inicjalizacja pakietu aplikacji
├── main.py                  # Główne uruchomienie FastAPI i rejestracja routerów
├── config.py                # Konfiguracja aplikacji (np. ustawienia bazy danych)
├── database.py              # Silnik SQLAlchemy, sesje, Base
├── models.py                # Modele ORM (SQLAlchemy)
├── schemas.py               # Schematy Pydantic do walidacji danych
├── crud.py                  # Logika operacji na bazie danych
└── routers/
    ├── __init__.py
    ├── users.py             # Endpointy użytkowników
    ├── appointments.py      # Endpointy wizyt
    ├── animals.py           # Endpointy zwierząt
    ├── medical_records.py   # Endpointy historii leczenia
    └── invoices.py          # Endpointy faktur
tests/
├── __init__.py
├── test_users.py            # Testy użytkowników
└── test_appointments.py     # Testy wizyt
requirements.txt             # Lista zależności projektu
README.md                    # Dokumentacja projektu
```

## Instalacja i uruchomienie

### 1. Klonowanie repozytorium

```bash
git clone https://github.com/PSK-projekty/Programowanie-Defensywne.git
cd Programowanie-Defensywne
```
### 2. Utworzenie i aktywacja środowiska wirtualnego (opcjonalnie, ale zalecane)
```bash
python -m venv venv
```
# Dla systemu Windows:
```bash
venv\Scripts\activate
```
# Dla systemów Linux/macOS
```bash:
source venv/bin/activate
```

### 3. Instalacja zależności
```bash
pip install -r requirements.txt
```

### 4. Uruchomienie aplikacji

```bash
uvicorn app.main:app --reload
```
Aplikacja będzie dostępna pod adresem: http://127.0.0.1:8000

## Testy

Projekt zawiera testy jednostkowe oraz integracyjne dla wybranych modułów aplikacji.

### Uruchamianie testów

Aby uruchomić testy, wykonaj poniższe polecenie z katalogu głównego projektu:

```bash
pytest
```

# Struktura testów
Testy znajdują się w katalogu tests/ i są podzielone według funkcjonalności, np:
```
tests/
├── __init__.py
├── test_users.py           # Testy rejestracji, logowania i pobierania użytkowników
└── test_appointments.py    # Testy tworzenia i odczytu wizyt
```

## Technologie

Projekt został zbudowany w oparciu o nowoczesny stos technologiczny Pythonowy:

- **Python 3.10+** – główny język programowania
- **FastAPI** – szybki i nowoczesny framework webowy do tworzenia API
- **SQLAlchemy** – ORM do mapowania modeli na bazę danych
- **Pydantic** – walidacja i serializacja danych wejściowych/wyjściowych
- **Uvicorn** – lekki serwer ASGI do uruchamiania aplikacji FastAPI
- **pytest** – framework do pisania i uruchamiania testów
- **SQLite** – domyślna baza danych w wersji lokalnej (możliwa zamiana na PostgreSQL)