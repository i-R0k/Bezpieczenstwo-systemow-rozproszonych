# Raport techniczny projektu

## 1. Cel projektu

Celem projektu jest implementacja i analiza demonstracyjnego systemu odpornego na bledy bizantyjskie z wykorzystaniem koncepcji Narwhal, HotStuff i SWIM. System pokazuje przeplyw operacji klienta przez data availability, konsensus, wykonanie stanu, checkpointing, recovery, zabezpieczenia komunikatow i observability.

Implementacja jest edukacyjna, in-memory i demonstracyjna. Nie jest produkcyjna implementacja BFT.

## 2. Architektura systemu

Warstwa BFT znajduje sie w `VetClinic/API/vetclinic_api/bft`, a publiczny router w `VetClinic/API/vetclinic_api/routers/bft.py`. Moduly sa rozdzielone wedlug odpowiedzialnosci: `common`, `narwhal`, `hotstuff`, `swim`, `fault_injection`, `checkpointing`, `recovery`, `crypto` i `observability`.

Gorna warstwa API wystawia endpointy `/bft/*`. Testbed uzywa minimalnej aplikacji FastAPI z samym routerem BFT, a osobny smoke test sprawdza rejestracje routera w pelnej aplikacji VetClinic.

## 3. Model operacji

Operacja klienta przechodzi przez statusy `RECEIVED`, `BATCHED`, `AVAILABLE`, `PROPOSED`, `VOTED`, `QC_FORMED`, `COMMITTED` i `EXECUTED`. Historia zmian jest dostepna przez trace operacji i event log.

Model jest celowo deterministyczny, aby testbed mogl sprawdzac kolejnosc przejsc bez prawdziwej sieci i bez zaleznosci czasowych.

## 4. Warstwa Narwhal

Narwhal odpowiada za grupowanie operacji w batch, lokalny DAG oraz certyfikat data availability. Batch zawiera identyfikatory operacji i hash payloadu. Certyfikat batcha powstaje po demonstracyjnym zebraniu quorum ACK zgodnie z `2f + 1`.

Implementacja nie wykonuje realnego broadcastu miedzy procesami. Jest lokalnym kontraktem pokazujacym, jakie dane HotStuff moze konsumowac.

## 5. Warstwa HotStuff

HotStuff tworzy proposal na bazie certyfikowanego batcha Narwhal, przyjmuje glosy, formuje quorum certificate i wykonuje commit. Obecny view-state przechowuje lidera, widok, high QC, locked QC i ostatni commit.

Endpointy `form-qc-demo` i `view-change-demo` symuluja zachowanie wielu wezlow lokalnie. To wystarcza do demonstracji reguly quorum i relacji Narwhal -> HotStuff.

## 6. Warstwa SWIM

SWIM utrzymuje membership logicznych wezlow BFT i statusy `ALIVE`, `SUSPECT`, `DEAD`, `RECOVERING`. Mechanizmy ping, ping-req i gossip sa modelowane przez serwis i endpointy.

Statusy SWIM sa wykorzystywane przez HotStuff: wezly `SUSPECT` i `DEAD` nie powinny uczestniczyc jako proposerzy lub glosujacy.

## 7. Fault injection

Fault injection pozwala wymusic drop, delay, duplicate, replay, equivocation, partition i leader failure. Reguly sa lokalne i in-memory, a decyzje sa widoczne w odpowiedziach endpointow oraz event logu.

Testy nie uzywaja realnych opoznien. `DELAY` jest zapisem decyzji, a nie `sleep`.

## 8. Checkpointing i recovery

Checkpointing tworzy deterministyczny snapshot stanu z operacji zatwierdzonych i wykonanych. Snapshot otrzymuje hash stanu, a certyfikat checkpointu potwierdza go demonstracyjnym quorum.

Recovery modeluje state transfer dla wezla po awarii lub korupcji stanu. Wezel moze przejsc do `RECOVERING`, pobrac checkpoint, zastosowac stan i wrocic do `ALIVE`.

## 9. Bezpieczenstwo komunikatow

Warstwa crypto wykorzystuje Ed25519, canonical JSON, `BftSignedMessage`, nonce, `message_id` i replay protection. Klucze demo sa generowane i przechowywane w pamieci.

Replay protection wykrywa ponowna weryfikacje tego samego komunikatu. Projekt nie zawiera produkcyjnego PKI ani pelnej konfiguracji mTLS.

## 10. Observability

Observability obejmuje health checki komponentow, metryki w formacie Prometheus, snapshot metryk i raport demo. Raport demo zawiera kroki, statusy, `operation_id`, `checkpoint_id`, `recovered_node_id` oraz `metrics_snapshot`.

## 11. Testbed automatyczny

Testbed znajduje sie w `tests/bft` i jest uruchamiany przez:

```powershell
python -m pytest tests/bft -q
python scripts/run_bft_testbed.py
```

Nie wymaga Dockera, uvicorn, GUI, Prometheus ani Grafany. Testy obejmuja kontrakty modulow, integracje, negatywne sciezki, router, final demo i dokumentacje.

## 12. Ograniczenia implementacji

Implementacja jest in-memory, demonstracyjna i edukacyjna. Nie ma trwalej bazy stanu BFT, prawdziwego transportu sieciowego BFT miedzy procesami, produkcyjnej konfiguracji mTLS ani paper-grade implementacji Narwhal, HotStuff i SWIM.

Pelna lista ograniczen znajduje sie w `docs/OGRANICZENIA.md`.

## 13. Mozliwe kierunki rozwoju

Naturalne kierunki rozwoju to trwaly storage BFT, osobne procesy wezlow, transport sieciowy z podpisami na kazdym komunikacie, produkcyjne mTLS, bardziej kompletny pipeline HotStuff, pelniejszy gossip SWIM i dashboard Grafana dedykowany BFT.

## 14. Instrukcja uruchomienia

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
```

## 15. Wnioski

Projekt domyka wymagany zakres demonstracyjny: pokazuje separacje data availability i konsensusu, failure detection, kontrolowane awarie, checkpointing, recovery, podpisy komunikatow, replay protection, observability i automatyczny testbed. Najwazniejsza wartoscia techniczna jest spojnosc kontraktow i mozliwosc powtarzalnej prezentacji bez zewnetrznej infrastruktury.
