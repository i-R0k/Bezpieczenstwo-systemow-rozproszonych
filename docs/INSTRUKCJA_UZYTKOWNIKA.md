# Instrukcja uzytkownika

## Wymagania

- Python 3.12.
- `pip`.
- Docker opcjonalnie, tylko do uruchomienia calego stosu Compose.

## Instalacja zaleznosci

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-api.txt
```

Jezeli pracujesz na pelnym zestawie zaleznosci repo:

```powershell
python -m pip install -r requirements.txt
```

## Uruchomienie testbedu

```powershell
python scripts/run_bft_testbed.py
```

Runner wypisuje sekcje testbedu BFT i konczy sie kodem wyjscia pytest. Nie uruchamia Dockera ani uvicorn.

Alternatywa:

```powershell
python -m pytest tests/bft -q
```

## Uruchomienie API lokalnie

```powershell
$env:PYTHONPATH="VetClinic/API"
python -m uvicorn vetclinic_api.main:app --host 127.0.0.1 --port 8001 --reload
```

## Uruchomienie Docker Compose

```powershell
docker compose up -d --build
docker compose ps
docker compose down
```

Compose uruchamia bazowe serwisy VetClinic. Do samego testbedu BFT Docker nie jest wymagany.

## Swagger UI

Po starcie API wejdz w przegladarce:

```text
http://127.0.0.1:8001/docs
```

Endpointy BFT sa w tagu `bft` i maja prefiks `/bft`.

## Uruchomienie demo przez endpoint

```powershell
curl.exe -X POST http://127.0.0.1:8001/bft/demo/run
curl.exe http://127.0.0.1:8001/bft/demo/last-report
```

Oczekiwany raport zawiera `status: ok`, `final_operation_status: EXECUTED`, `checkpoint_id`, `recovered_node_id` i `metrics_snapshot`.

## Odczyt metryk

```powershell
curl.exe http://127.0.0.1:8001/bft/observability/health
curl.exe http://127.0.0.1:8001/bft/observability/metrics
curl.exe http://127.0.0.1:8001/bft/observability/metrics/snapshot
```

`/metrics` zwraca tekst w formacie Prometheus.

## Najczestsze problemy

- `ModuleNotFoundError: vetclinic_api`: ustaw `$env:PYTHONPATH="VetClinic/API"` albo uruchom testy przez dostarczony testbed.
- Brak `uvicorn`: zainstaluj `requirements-api.txt`.
- Port 8001 zajety: uruchom uvicorn z innym portem, np. `--port 8010`.
- Docker nie dziala: uzyj lokalnego testbedu, bo BFT nie wymaga Dockera.
- Demo zwraca blad: uruchom najpierw `python -m pytest tests/bft -q`, zeby sprawdzic kontrakty modulow.
- Zakladka `Siec` pokazuje `INVALID`: rozwin kolumne `Faults`. Komunikat `invalid leader_sig for leader_id=X` oznacza bledny podpis dla konkretnego lidera, a `stale chain format: missing leader_id` oznacza stary demo chain sprzed jawnego pola `leader_id`.
