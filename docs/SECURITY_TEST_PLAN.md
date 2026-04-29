# Security test plan

## Cel

Plan opisuje fundament programu testow bezpieczenstwa dla calego projektu. Deterministyczne testy pytest sa podstawa, bo dzialaja lokalnie bez Dockera, uvicorn, Prometheus i Grafany. Bandit, pip-audit, Semgrep, Trivy i ZAP sa dodatkowymi warstwami SAST/SCA/DAST/infra scan.

## Tryb demo i strict

Warstwa BFT ma demonstracyjny tryb bezpieczenstwa sterowany zmiennymi srodowiskowymi:

- `BFT_SECURITY_MODE=demo` - domyslny tryb zgodny z demonstracja; endpointy administracyjne dzialaja bez tokena.
- `BFT_SECURITY_MODE=strict` - endpointy administracyjne i destrukcyjne wymagaja naglowka `X-BFT-Admin-Token`.
- `BFT_ADMIN_TOKEN` - wartosc tokena wymagana w strict mode. Brak tej zmiennej w strict mode jest traktowany jako misconfiguration.

Strict mode nie jest pelnym IAM. Chroni demo endpointy administracyjne przed przypadkowym lub nieautoryzowanym uzyciem i stanowi baze pod dalsze testy Broken Function Level Authorization.

Endpointy publiczne, takie jak `GET /bft/status`, `GET /bft/architecture`, `GET /bft/protocols`, `GET /bft/observability/health` i `GET /bft/observability/metrics`, pozostaja dostepne bez tokena, o ile nie ujawniaja sekretow.

## Tabela testow

| Component | Risk | Test file | Expected result | Tool |
|---|---|---|---|---|
| VetClinic API | BOLA, broken authentication, mass assignment, validation bypass | `tests/security/test_10_api_auth_authz.py` | Brak dostepu do cudzych zasobow i funkcji bez roli | pytest, ZAP |
| BFT API | Nieautoryzowane operacje BFT, resource abuse, brak limitow | `tests/security/test_20_bft_api_security.py` | Endpointy nie zwracaja 500 i odrzucaja zle payloady | pytest |
| Blockchain/RPC/Cluster | Nieautoryzowane RPC, forged node call, manipulacja klastrem | `tests/security/test_30_blockchain_rpc_cluster.py` | Krytyczne funkcje wymagaja kontroli dostepu w trybie strict | pytest, ZAP |
| Admin/Fault endpoints | Unauthorized fault injection, broken function level authorization | `tests/security/test_40_admin_fault_abuse.py` | Endpointy admin/fault sa blokowane bez tokena w trybie strict | pytest |
| Crypto/Replay/Equivocation | Replay, forged vote/proposal/checkpoint, equivocation | `tests/security/test_09_crypto_replay_equivocation.py` | Replay i falszywe podpisy sa wykrywane | pytest |
| Checkpointing/Recovery | State corruption, nieautoryzowany state transfer | `tests/security/test_10_checkpoint_recovery_security.py` | Recovery akceptuje tylko spojny checkpoint/state hash | pytest |
| Database/SQLAlchemy | SQL injection, nadmiarowe uprawnienia, leakage | `tests/security/test_70_database_security.py` | Parametryzacja i brak wycieku danych | pytest, Semgrep |
| Docker/Compose | Otwarte porty, sekrety, brak healthcheck, default credentials | `tests/security/test_80_infra_static.py` | Compose nie ujawnia sekretow i ma jawne porty | pytest, Trivy |
| Monitoring | Publiczne metryki, leakage, Grafana default auth | `tests/security/test_81_monitoring_static.py` | Monitoring nie ujawnia sekretow | pytest, Trivy |
| GUI | Niebezpieczne przechowywanie tokenow, brak walidacji klienta | `tests/security/test_90_gui_static.py` | GUI nie przechowuje sekretow jawnie | pytest, Semgrep |
| Dependencies | Podatne pakiety PyPI, supply chain | `tests/security/test_95_dependencies.py` | Raport SCA bez krytycznych podatnosci albo jawne wyjatki | pip-audit |
| Secrets | `.env`, tokeny, klucze, hasla w repo | `tests/security/test_96_secrets.py` | Brak sekretow w repo i logach | pytest, Semgrep |
| CI | Zbyt szerokie permissions, brak security jobow, pominiete testy | `tests/security/test_97_ci_security.py` | Workflow uruchamia testy i nie pomija `tests/bft`/`tests/security` | pytest |

## Aktualne pliki testow security

- `tests/security/test_00_security_smoke.py` - smoke test klientow, `/bft/status`, pelnej aplikacji i dokumentow.
- `tests/security/test_01_api_authentication.py` - demo/strict mode, `BFT_ADMIN_TOKEN`, `X-BFT-Admin-Token`.
- `tests/security/test_02_api_authorization.py` - blokada destrukcyjnych endpointow BFT w strict mode.
- `tests/security/test_03_api_input_validation.py` - walidacja payloadow BFT i fault injection.
- `tests/security/test_04_vetclinic_business_logic.py` - VetClinic CRUD, IDOR smoke, mass assignment, kwoty, referencje i dlugie opisy.
- `tests/security/test_05_sqlalchemy_sqli_contract.py` - payloady SQL injection i statyczny skan f-string/raw SQL.
- `tests/security/test_06_blockchain_rpc_security.py` - legacy blockchain/RPC/cluster, forged payloads i brak sekretow.
- `tests/security/test_07_admin_cluster_security.py` - admin/network demo vs strict i walidacja niepoprawnego state.
- `tests/security/test_08_bft_protocol_security.py` - ataki na Narwhal/HotStuff/SWIM: batch bez certyfikatu, commit bez QC, glosy wezlow DEAD/SUSPECT/RECOVERING oraz fault rules blokujace quorum.
- `tests/security/test_09_crypto_replay_equivocation.py` - forged signatures, tampering message body/nonce/source, unknown key, replay glosow/ACK/recovery oraz equivocation proposer/view/block.
- `tests/security/test_10_checkpoint_recovery_security.py` - invalid checkpoint, forged checkpoint certificate lookup, recovery z nieistniejacego checkpointu i glosowanie wezla RECOVERING.
- `tests/security/test_11_fault_injection_abuse_security.py` - DROP/DELAY/DUPLICATE fault abuse, probability 0/1 i czyszczenie fault injection state.
- `tests/security/test_12_swim_membership_security.py` - stale gossip, monotonic incarnation, DEAD precedence i kontrolowane ping error cases.
- `tests/security/test_13_secrets_config_contract.py` - brak `.env`, brak prywatnych plikow kluczy i brak sekretow w publicznych odpowiedziach BFT.
- `tests/security/test_14_container_config_security.py` - statyczne kontrole `docker-compose.yml`, `Dockerfile.api`, portow Prometheus/Grafana i trybu non-root.
- `tests/security/test_15_monitoring_exposure.py` - brak sekretow w health/metrics, Prometheus i Grafana provisioning.
- `tests/security/test_16_gui_static_security.py` - statyczny skan GUI pod katem `eval`, `exec`, hardcoded secrets, URL i logowania Authorization.
- `tests/security/test_17_sast_sca_wrappers.py` - kontrakt `requirements-security.txt`, workflow security i lokalnego wrappera narzedzi.
- `tests/security/test_15_error_handling_information_leakage.py` - brak tracebackow, sciezek, SQLAlchemy errors i sekretow w odpowiedziach.
- `tests/security/test_16_resource_abuse_dos_limits.py` - limity list, batch size, payload depth i petla 100 operacji.

## BFT protocol attack tests

Testy BFT w `tests/security` traktuja protokoly jako powierzchnie ataku, a nie tylko happy-path kontrakty. Zakres obejmuje:

- forged signatures: zmiana body, nonce, source node i public key po podpisaniu musi byc odrzucona przez warstwe crypto;
- replay protection: ponowna weryfikacja tego samego komunikatu, replay vote, batch ACK i recovery nie moga zmieniac stanu drugi raz;
- equivocation: ten sam proposer i view z roznym `block_id` jest konfliktem, natomiast inny view albo proposer nie powinien generowac falszywego alarmu;
- forged proposal/vote/commit: HotStuff nie akceptuje propozycji dla batcha bez `BatchCertificate`, commitu bez QC, podwojnego commitu ani glosow wezlow DEAD/SUSPECT/RECOVERING;
- invalid checkpoint/state transfer: recovery bez certyfikowanego checkpointu, nieistniejacy checkpoint i checkpoint z niewystarczajacym quorum sa kontrolowanie odrzucane;
- fault injection abuse: DROP/DELAY/DUPLICATE oraz NETWORK_PARTITION nie moga powodowac 500 ani obchodzic quorum/idempotencji;
- SWIM membership attacks: starszy gossip jest ignorowany, nowsza incarnation jest stosowana, a DEAD przy tej samej incarnation ma pierwszenstwo nad ALIVE.

## SAST

Bandit jest podstawowym blocking skanerem statycznym w `.github/workflows/security-tests.yml` po instalacji `requirements-security.txt`. Lokalnie mozna uruchomic:

```powershell
python scripts/run_security_tools.py
```

Semgrep jest wlaczony jako warstwa dodatkowa i na start ma `continue-on-error: true`, zeby raportowal ryzyka bez blokowania calego projektu.

## SCA

`pip-audit -r requirements-api.txt` sprawdza podatnosci zaleznosci API i jest blocking w workflow security po instalacji narzedzi. Zaleznosci security sa odseparowane w `requirements-security.txt`, zeby nie rozszerzac podstawowego testbedu BFT/API.

## DAST

ZAP baseline jest manualnym workflow `.github/workflows/zap-baseline.yml`. Workflow uruchamia API lokalnie, czeka na `/bft/observability/health`, wykonuje baseline scan przeciwko `http://localhost:8000` i jest non-blocking (`fail_action: false`).
Ten sam workflow wykonuje takze ZAP API scan po OpenAPI `http://localhost:8000/openapi.json`. Artefakty sa uploadowane osobno jako `zap-baseline-report` i `zap-api-report`, z raportami HTML/JSON.

Lokalnie `scripts/run_pentest_local.py` uruchamia ZAP baseline w quick mode, a w full mode dodaje ZAP API scan. High severity z raportu JSON jest kandydatem na przyszly gate, ale workflow pozostaje manualny i non-blocking, dopoki findings nie zostana przejrzane i false positives nie beda opisane w konfiguracji.

## Pentest harness

Osobna warstwa pentest znajduje sie w `pentest/` i jest uruchamiana przez:

```powershell
python scripts/run_pentest_local.py --quick
python scripts/run_pentest_local.py --full
```

Quick mode startuje lokalny FastAPI target, czeka na `/bft/observability/health`, wykonuje lekkie probe HTTP (`/openapi.json`, `/bft/status`, health/metrics, dotfiles, `/admin`, `/debug`) oraz sprawdza metody `OPTIONS` i `TRACE` na kilku sciezkach.

Full mode uruchamia quick mode i dodatkowo probuje uzyc ZAP baseline, Nuclei oraz ffuf, jesli narzedzia sa dostepne w PATH. Brak narzedzia jest raportowany jako `skipped`, bez blokowania podstawowego harnessu.

Raporty sa zapisywane w `reports/pentest/<timestamp>/` jako `metadata.json` i `summary.md`. Harness ma localhost-only safety guard: dozwolone targety to tylko `http://127.0.0.1:8000` albo `localhost`; hosty zewnetrzne sa odrzucane przed skanem.

Nuclei w pentest harnessie uzywa wlasnych template'ow z `pentest/nuclei/` dla ekspozycji specyficznych dla projektu: BFT demo endpoints, admin/demo controls, FastAPI docs, local metrics oraz sensitive files. Findings `high` i `critical` z `nuclei.jsonl` sa przenoszone do `summary.md` jako high severity; `info`, `low` i `medium` sa raportowane do triage.

## Secret scanning

Testy pytest sprawdzaja brak `.env`, brak prywatnych plikow `*.pem`, `*.key`, `id_rsa`, `id_dsa` oraz brak sekretow w `/bft/status`, `/bft/crypto/public-keys`, `/bft/crypto/demo-keys`, health i metrics. Trivy secret scan jest dodatkowa, non-blocking warstwa w workflow.

## Container/IaC scanning

Statyczne testy kontenerow sprawdzaja brak `privileged: true`, `network_mode: host`, montowania `/var/run/docker.sock`, remote `ADD`, `DEBUG=1` i wymuszaja non-root runtime w `Dockerfile.api`. Trivy `fs --scanners vuln,secret,misconfig` jest non-blocking w workflow.

## Monitoring exposure

Prometheus `9090` i Grafana `3000` sa traktowane jako lokalne porty demo. Testy sprawdzaja, ze konfiguracje Prometheus/Grafana oraz endpointy BFT health/metrics nie zawieraja sekretow.

## GUI static security

GUI PyQt jest skanowane statycznie bez uruchamiania PyQt. Testy szukaja niebezpiecznych konstrukcji `eval`, builtin `exec`, hardcoded secrets, nieoczekiwanych zewnetrznych URL i logowania naglowka Authorization.

## Etapy wdrazania

1. Smoke test security testbedu i dokumentow.
2. Testy auth/authz dla VetClinic API i admin endpoints.
3. Testy walidacji inputow i limitow zasobow.
4. Testy BFT protocol security: replay, forged message, equivocation, checkpoint consistency.
5. Testy statyczne Docker/Compose, monitoring, GUI, secrets i CI.
6. Wrappery narzedzi: Bandit, pip-audit, Semgrep, Trivy i ZAP.
