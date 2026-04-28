# Bezpieczenstwo systemow rozproszonych - demonstrator BFT

## Co to jest

Projekt jest demonstracyjnym systemem BFT przygotowanym na potrzeby przedmiotu Bezpieczenstwo systemow rozproszonych. Warstwa `/bft` pokazuje przeplyw operacji przez Narwhal, HotStuff, SWIM, fault injection, checkpoint, recovery, crypto, observability oraz automatyczny testbed.

VetClinic pozostaje domena przykladowa i starsza warstwa aplikacyjna. BFT jest osobna warstwa demonstracyjna w `VetClinic/API/vetclinic_api/bft` oraz `VetClinic/API/vetclinic_api/routers/bft.py`.

## Najwazniejsze funkcje

- Narwhal: batchowanie, DAG i data availability.
- HotStuff: proposal, vote, quorum certificate, commit i view-change.
- SWIM: membership oraz failure detection.
- fault injection: DROP, DELAY, DUPLICATE, REPLAY, EQUIVOCATION, NETWORK_PARTITION.
- checkpoint i recovery: snapshot stanu, checkpoint certificate, state transfer i odtworzenie wezla.
- crypto: Ed25519, canonical JSON, podpisy i replay protection.
- observability: health, metryki i raport demo.
- testbed: automatyczne testy kontraktowe i integracyjne bez Dockera.

## Szybki start bez Dockera

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-api.txt
python scripts/run_bft_testbed.py
```

## Testy

```powershell
make test-bft
make test-bft-contract
python -m pytest tests/bft -q
```

## Uruchomienie API

Z katalogu repo:

```powershell
$env:PYTHONPATH="VetClinic/API"
uvicorn vetclinic_api.main:app --reload
```

Albo z katalogu API:

```powershell
cd VetClinic/API
uvicorn vetclinic_api.main:app --reload
```

Swagger UI jest dostepny pod `/docs`.

## Docker Compose

Docker Compose uruchamia bazowe serwisy projektu VetClinic. Testbed BFT nie wymaga Dockera.

```powershell
docker compose up -d --build
```

## Demo

Po uruchomieniu API:

```text
POST /bft/demo/run
GET  /bft/demo/last-report
```

Raport demo powinien zawierac `status=ok`, `final_operation_status=EXECUTED`, `checkpoint_id`, `recovered_node_id` i `metrics_snapshot`.

## Dokumentacja

- `docs/ARCHITEKTURA.md`
- `docs/NARWHAL.md`
- `docs/HOTSTUFF.md`
- `docs/SWIM.md`
- `docs/FAULT_INJECTION.md`
- `docs/CHECKPOINTING_RECOVERY.md`
- `docs/CRYPTO_SECURITY.md`
- `docs/OBSERVABILITY.md`
- `docs/DEMO.md`
- `docs/TESTBED.md`
- `docs/ZGODNOSC_Z_HARMONOGRAMEM.md`
- `docs/RAPORT_TECHNICZNY.md`
- `docs/INSTRUKCJA_UZYTKOWNIKA.md`
- `docs/SCENARIUSZ_PREZENTACJI.md`
- `docs/API_BFT.md`
- `docs/OGRANICZENIA.md`

## Ograniczenia

Implementacja jest demonstracyjna, edukacyjna i in-memory. Nie jest produkcyjnym systemem BFT, nie ma produkcyjnego mTLS, trwalej bazy stanu BFT ani paper-grade implementacji Narwhal/HotStuff/SWIM. Szczegoly sa opisane w `docs/OGRANICZENIA.md`.
