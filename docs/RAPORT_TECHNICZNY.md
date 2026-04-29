# Raport techniczny projektu

## 1. Cel projektu

Celem projektu jest implementacja i analiza demonstracyjnego systemu odpornego na bledy bizantyjskie z wykorzystaniem koncepcji Narwhal, HotStuff i SWIM. System pokazuje przeplyw operacji klienta przez data availability, konsensus, wykonanie stanu, checkpointing, recovery, zabezpieczenia komunikatow, observability, testy security i lokalny pentest harness.

Implementacja jest edukacyjna, in-memory i demonstracyjna. Nie jest produkcyjna implementacja BFT.

## 2. Architektura systemu

Warstwa BFT znajduje sie w `VetClinic/API/vetclinic_api/bft`, a publiczny router w `VetClinic/API/vetclinic_api/routers/bft.py`. Moduly sa rozdzielone wedlug odpowiedzialnosci: `common`, `narwhal`, `hotstuff`, `swim`, `fault_injection`, `checkpointing`, `recovery`, `crypto`, `observability` i `grpc_contract`.

Gorna warstwa API wystawia endpointy `/bft/*`. Pelna aplikacja FastAPI rejestruje rowniez router `security_demo` dla minimalnego TOTP/2FA.

## 3. Model operacji

Operacja klienta przechodzi przez statusy `RECEIVED`, `BATCHED`, `AVAILABLE`, `PROPOSED`, `VOTED`, `QC_FORMED`, `COMMITTED` i `EXECUTED`. Historia zmian jest dostepna przez trace operacji i event log.

Model jest deterministyczny, aby testbed mogl sprawdzac kolejnosc przejsc bez prawdziwej sieci i bez zaleznosci czasowych.

## 4. Warstwa Narwhal

Narwhal odpowiada za grupowanie operacji w batch, lokalny DAG oraz certyfikat data availability. Batch zawiera identyfikatory operacji i hash payloadu. Certyfikat batcha powstaje po demonstracyjnym zebraniu quorum ACK zgodnie z `2f + 1`.

Implementacja nie wykonuje realnego broadcastu miedzy procesami. Jest lokalnym kontraktem pokazujacym, jakie dane HotStuff moze konsumowac.

## 5. Warstwa HotStuff

HotStuff tworzy proposal na bazie certyfikowanego batcha Narwhal, przyjmuje glosy, formuje quorum certificate i wykonuje commit. Obecny view-state przechowuje lidera, widok, high QC, locked QC i ostatni commit.

Endpointy `form-qc-demo` i `view-change-demo` symuluja zachowanie wielu wezlow lokalnie. Pacemaker jest uproszczony do deterministycznej zmiany widoku/lidera.

## 6. Warstwa SWIM

SWIM utrzymuje membership logicznych wezlow BFT i statusy `ALIVE`, `SUSPECT`, `DEAD`, `RECOVERING`. Mechanizmy ping, ping-req i gossip sa modelowane przez serwis i endpointy.

Statusy SWIM sa wykorzystywane przez HotStuff: wezly `SUSPECT`, `DEAD` i `RECOVERING` sa traktowane jako ryzykowne w sciezkach glosowania/proponowania.

## 7. Fault injection

Fault injection pozwala wymusic drop, delay, duplicate, replay, equivocation, partition i leader failure. Reguly sa lokalne i in-memory, a decyzje sa widoczne w odpowiedziach endpointow oraz event logu.

Testy nie uzywaja realnych opoznien. `DELAY` jest zapisem decyzji, a nie `sleep`.

## 8. Checkpointing i recovery

Checkpointing tworzy deterministyczny snapshot stanu z operacji zatwierdzonych i wykonanych. Snapshot otrzymuje hash stanu, a certyfikat checkpointu potwierdza go demonstracyjnym quorum.

Recovery modeluje state transfer dla wezla po awarii lub korupcji stanu. Wezel moze przejsc do `RECOVERING`, pobrac checkpoint, zastosowac stan i wrocic do `ALIVE`.

## 9. Bezpieczenstwo komunikatow

Warstwa crypto wykorzystuje Ed25519, canonical JSON, `BftSignedMessage`, nonce, `message_id` i replay protection. Klucze demo sa generowane i przechowywane w pamieci.

Replay protection wykrywa ponowna weryfikacje tego samego komunikatu. Projekt nie zawiera produkcyjnego PKI.

## 10. gRPC contract

`proto/bft.proto` definiuje kontrakt transportowy `BftNodeService` dla docelowej komunikacji node-to-node. Obejmuje komunikaty Narwhal, HotStuff, SWIM i state transfer.

Endpoint `/bft/grpc/contract` zwraca sciezke proto, nazwe serwisu, liste metod i `implementation_level=contract-only`. FastAPI/in-memory testbed pozostaje podstawowa sciezka wykonania.

## 11. mTLS demo tooling

`scripts/generate_demo_certs.py` generuje demo CA oraz certyfikaty dla node1..nodeN. `docs/MTLS.md` opisuje roznice miedzy message-level signing a mTLS, a `docker-compose.override.tls.example.yml` pokazuje przyklad uruchomienia TLS.

Domyslny runtime nie wymusza mTLS. Endpoint `/bft/security/transport` jawnie zwraca `mtls_runtime_enabled=false`.

## 12. TOTP/2FA demo

Moduly `vetclinic_api.security.totp` i `totp_store` oraz router `/security/2fa/demo/*` pokazuja minimalny flow TOTP. Setup zwraca secret i provisioning URI, a verify sprawdza kod.

W strict mode endpoint `/bft/client/submit-secure-demo` wymaga poprawnego TOTP. To demonstracja, nie pelny enrollment uzytkownika.

## 13. Dashboard i communication log

`/bft/dashboard` serwuje statyczny HTML dashboard pokazujacy nodes, SWIM membership, HotStuff, Narwhal, fault injection, checkpoint/recovery, crypto/security, recent events i communication log.

`/bft/communication/log` buduje logiczny dziennik komunikacji z `EventLog`. Nie jest to przechwytywanie pakietow sieciowych.

## 14. Observability

Observability obejmuje health checki komponentow, metryki w formacie Prometheus, snapshot metryk i raport demo. Raport demo zawiera kroki, statusy, `operation_id`, `checkpoint_id`, `recovered_node_id` oraz `metrics_snapshot`.

## 15. Security and pentest coverage

`tests/security` obejmuje API auth/authz, input validation, VetClinic business logic, legacy blockchain/RPC/cluster, BFT attack cases, replay/equivocation, checkpoint/recovery security, secrets/config, containers, monitoring, GUI, mTLS i TOTP.

`pentest/` oraz `scripts/run_pentest_local.py` tworza lokalny DAST harness z lightweight probes oraz opcjonalnymi ZAP, Nuclei i ffuf. Skany sa ograniczone do localhost/127.0.0.1.

## 16. Testbed automatyczny

Testbed znajduje sie w `tests/bft` i jest uruchamiany przez:

```powershell
python -m pytest tests/bft -q
python scripts/run_bft_testbed.py
```

Nie wymaga Dockera, uvicorn, GUI, Prometheus ani Grafany.

## 17. Ograniczenia implementacji

Implementacja jest in-memory, demonstracyjna i edukacyjna. Nie ma trwalej bazy stanu BFT, prawdziwego transportu sieciowego BFT miedzy procesami, aktywnego runtime gRPC, produkcyjnej konfiguracji mTLS ani paper-grade implementacji Narwhal, HotStuff i SWIM.

Pelna lista ograniczen znajduje sie w `docs/OGRANICZENIA.md`.

## 18. Mozliwe kierunki rozwoju

Naturalne kierunki rozwoju to trwaly storage BFT, osobne procesy wezlow, runtime gRPC, produkcyjne mTLS, bardziej kompletny pipeline HotStuff, pelniejszy gossip SWIM, WebSocket dashboard i rozszerzone raportowanie pentestowe.

## 19. Instrukcja uruchomienia

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-api.txt
python scripts/run_bft_testbed.py
```

API lokalne:

```powershell
$env:PYTHONPATH="VetClinic/API"
python -m uvicorn vetclinic_api.main:app --host 127.0.0.1 --port 8001 --reload
```

Demo API:

```powershell
curl.exe -X POST http://127.0.0.1:8001/bft/demo/run
curl.exe http://127.0.0.1:8001/bft/demo/last-report
curl.exe http://127.0.0.1:8001/bft/dashboard
```

## 20. Wnioski

Projekt domyka wymagany zakres demonstracyjny: pokazuje separacje data availability i konsensusu, failure detection, kontrolowane awarie, checkpointing, recovery, podpisy komunikatow, replay protection, observability, gRPC contract, mTLS tooling, TOTP demo, dashboard oraz automatyczne testy BFT/security/pentest. Najwazniejsza wartoscia techniczna jest spojnosc kontraktow i mozliwosc powtarzalnej prezentacji bez zewnetrznej infrastruktury.
