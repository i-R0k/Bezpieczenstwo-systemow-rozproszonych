# Strategia testowania i wyniki analizy kodu

## 1. Wprowadzenie

Dokument ten opisuje przyjętą strategię testowania aplikacji **VetClinic** oraz sposób integrowania wyników testów z analizą statyczną w SonarCloud. Zawiera instrukcje uruchamiania testów, konfigurację narzędzi oraz podsumowanie bieżących metryk jakości kodu.

---

## 2. Narzędzia i środowisko

* **pytest** : framework do uruchamiania testów jednostkowych.
* **pytest-cov** : plugin do generowania raportu pokrycia kodu.
* **SQLite (test.db)** : baza danych używana lokalnie w testach.
* **SonarCloud** : chmurowa analiza statyczna i raportowanie metryk.
* **GitHub Actions** : CI/CD pipeline uruchamiający testy i skan SonarCloud.

### 2.1. Struktura katalogów

```text
VetClinic/
├── API/
│   ├── vetclinic_api/
│   ├── tests/            # testy jednostkowe
│   └── conftest.py       # konfiguracja pytest
├── requirements.txt      # zależności runtime
└── requirements-dev.txt  # zależności developerskie (pytest, pytest-cov)
```

---

## 3. Uruchamianie testów lokalnie

1. Upewnij się, że masz zainstalowane wymagane pakiety:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
2. W katalogu głównym projektu uruchom:
   ```bash
   export PYTHONPATH=$PYTHONPATH:./VetClinic/API
   pytest --cov=VetClinic --cov-report=xml
   ```
3. Raport pokrycia zostanie zapisany w pliku `coverage.xml` oraz wyświetlony w konsoli.

### 3.1. Struktura testów

* Każdy moduł ma odpowiadający plik testowy w `API/tests/`, np. `test_animals.py`, `test_users.py`.
* W `conftest.py` definiowane są:
  * testowa baza SQLite (`test.db`),
  * override dependency `get_db`,
  * automatyczne czyszczenie tabel (fixture `clean_all_tables`).

---

## 4. Strategia testów

### 4.1. Typy testów

* **Unit tests** : sprawdzają pojedyncze funkcje CRUD, walidatory i serwisy.
* **Integration tests** : poprzez FastAPI TestClient weryfikują zachowanie endpointów REST.
* **Smoke tests** : podstawowe uruchomienie aplikacji oraz testy bazy danych.

### 4.2. Pokrycie kodu

* Cel minimalny: **80%** pokrycia.
* Obecne pokrycie: **82%** (stan na ostatni build).
* Raport można znaleźć w `coverage.xml` lub w dashboardzie SonarCloud.

---

## 5. Integracja z SonarCloud

### 5.1. Konfiguracja

W pliku `sonar-project.properties`:

```properties
sonar.projectKey=PSK-projekty_Programowanie-Defensywne
sonar.organization=psk-projekty
sonar.sources=VetClinic/API
sonar.python.coverage.reportPaths=coverage.xml
sonar.host.url=https://sonarcloud.io
```

### 5.2. CI/CD (GitHub Actions)

```yaml
- name: Run tests and generate coverage
  run: |
    export PYTHONPATH=$PYTHONPATH:./VetClinic/API
    pytest --cov=VetClinic --cov-report=xml

- name: SonarCloud Scan
  uses: SonarSource/sonarqube-scan-action@v5.0.0
  with:
    args: >
      -Dsonar.projectKey=PSK-projekty_Programowanie-Defensywne
      -Dsonar.organization=psk-projekty
      -Dsonar.sources=VetClinic/API
      -Dsonar.host.url=https://sonarcloud.io
      -Dsonar.python.coverage.reportPaths=coverage.xml
  env:
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

### 5.3. Quality Gate

* Wyłączona opcja **Automatic Analysis** w SonarCloud.
* Analiza uruchamiana tylko w CI.
* Quality Gate: brak blockerów, <5% duplikacji kodu.

---

## 6. Podsumowanie wyników analizy

| Metryka                          | Wartość |
| -------------------------------- | --------: |
| Bugów (Blocker/Critical)        |         0 |
| Code Smells                      |        12 |
| Technical Debt (główny branch) |     1d 2h |
| Pokrycie kodu (Coverage)         |       82% |
| Duplikacja kodu                  |      3.1% |

> Dane zgodnie z raportem SonarCloud (ostatnia analiza).

---

## 7. Dalsze kroki

1. Uzupełnienie testów dla validatorów i edge cases.
2. Obniżenie Technical Debt poprzez refaktoryzację krytycznych code smells.
3. Rozszerzenie Quality Gate o limity dla złożoności cyklomatycznej i brak dokumentacji.
