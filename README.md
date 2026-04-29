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
- gRPC/protobuf contract: `proto/bft.proto` i endpoint `/bft/grpc/contract` jako kontrakt docelowej komunikacji node-to-node.
- TLS/mTLS demo tooling: generator certyfikatow w `scripts/generate_demo_certs.py` i status `/bft/security/transport`.
- 2FA/TOTP demo: `/security/2fa/demo/*` i opcjonalny `/bft/client/submit-secure-demo`.
- dashboard BFT: `/bft/dashboard` oraz logiczny dziennik `/bft/communication/log`.
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

## Testy bezpieczenstwa

Security testbed obejmuje caly projekt: VetClinic API, legacy blockchain/RPC/cluster/admin endpoints, BFT `/bft/*`, Docker/Compose, monitoring, GUI, dependencies, secrets i CI. Obecny etap dodaje fundament smoke testow oraz dokumenty planujace zakres.

```powershell
python scripts/run_security_testbed.py
make test-security
make test-security-infra
python scripts/run_security_tools.py
```

Zakres i model zagrozen:

- `docs/THREAT_MODEL.md`
- `docs/SECURITY_TEST_PLAN.md`

`scripts/run_security_tools.py` uruchamia lokalnie pytest security, Bandit i pip-audit, a Semgrep oraz Trivy tylko wtedy, gdy sa dostepne w PATH. ZAP baseline jest osobnym, manualnym workflow `.github/workflows/zap-baseline.yml`; na tym etapie jest non-blocking i generuje raport demonstracyjny.

### Certyfikaty demo TLS/mTLS

```powershell
make generate-demo-certs
python scripts/generate_demo_certs.py --nodes 6 --out certs/demo --force
```

Domyslny runtime nie wymusza mTLS. Endpoint `/bft/security/transport` pokazuje `mtls_runtime_enabled=false`; szczegoly sa w `docs/MTLS.md`.

### 2FA/TOTP demo

```powershell
python -m pytest tests/security/test_19_totp_2fa_contract.py -q
```

Endpointy `/security/2fa/demo/setup` i `/security/2fa/demo/verify` pokazuja minimalny flow TOTP. W strict mode `/bft/client/submit-secure-demo` wymaga poprawnego kodu TOTP.

## Testy penetracyjne

Pentest harness uruchamia kontrolowane, lokalne skany DAST. Safety guard ogranicza targety do `localhost` i `127.0.0.1`; nie sluzy do testowania cudzych hostow.

```powershell
python scripts/run_pentest_local.py --quick
make pentest-quick
make pentest-zap
make pentest-full
make test-pentest
```

Tryb `--quick` uruchamia tylko lekkie probe HTTP. `make pentest-zap` dodaje ZAP baseline. Tryb `--full` dodaje ZAP baseline/API scan oraz opcjonalne Nuclei i ffuf, jesli sa dostepne lokalnie. Koncowy raport powstaje jako `reports/pentest/<timestamp>/PENTEST_REPORT.md`. Szczegoly i zasady uzycia sa w `pentest/README.md` oraz `docs/PENTEST.md`.

### Strict mode dla endpointow administracyjnych

Domyslnie projekt dziala w trybie demo:

```powershell
$env:BFT_SECURITY_MODE="demo"
```

W trybie strict endpointy administracyjne i destrukcyjne BFT wymagaja naglowka `X-BFT-Admin-Token`:

```powershell
$env:BFT_SECURITY_MODE="strict"
$env:BFT_ADMIN_TOKEN="change-me"
curl.exe -H "X-BFT-Admin-Token: change-me" http://127.0.0.1:8000/bft/status
```

Token nie jest pelnym IAM; to demonstracyjny hardening do testow auth/authz.

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
Prometheus `9090` i Grafana `3000` sa lokalnymi portami demo do obserwowalnosci, a klucze w `docker-compose.yml` sa wartosciami demonstracyjnymi do wymiany poza trybem laboratoryjnym.

```powershell
docker compose up -d --build
```

## Demo

Po uruchomieniu API:

```text
POST /bft/demo/run
GET  /bft/demo/last-report
GET  /bft/dashboard
GET  /bft/communication/log
```

Raport demo powinien zawierac `status=ok`, `final_operation_status=EXECUTED`, `checkpoint_id`, `recovered_node_id` i `metrics_snapshot`.

## Zgodnosc z harmonogramem

Glowne dokumenty zamykajace harmonogram:

- `docs/ZGODNOSC_Z_HARMONOGRAMEM.md`
- `docs/GRPC.md`
- `docs/MTLS.md`
- `docs/2FA_TOTP.md`
- `docs/GUI_BFT.md`
- `docs/PENTEST.md`

Komendy prezentacyjne:

```powershell
python scripts/run_bft_testbed.py
python scripts/run_security_testbed.py
python scripts/run_pentest_local.py --quick
python scripts/generate_demo_certs.py --nodes 2 --out /tmp/bsr-certs --force
```

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
- `docs/THREAT_MODEL.md`
- `docs/SECURITY_TEST_PLAN.md`
- `docs/PENTEST.md`
- `docs/GRPC.md`
- `docs/MTLS.md`
- `docs/2FA_TOTP.md`
- `docs/GUI_BFT.md`

## Ograniczenia

Implementacja jest demonstracyjna, edukacyjna i in-memory. Nie jest produkcyjnym systemem BFT, nie ma produkcyjnie wymuszonego mTLS, trwalej bazy stanu BFT ani paper-grade implementacji Narwhal/HotStuff/SWIM. gRPC jest obecnie kontraktem `.proto`, mTLS toolingiem demo, a 2FA/TOTP minimalnym flow in-memory. Szczegoly sa opisane w `docs/OGRANICZENIA.md`.
