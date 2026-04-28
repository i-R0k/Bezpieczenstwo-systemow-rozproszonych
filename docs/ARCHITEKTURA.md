# Architektura projektu

Ten dokument opisuje pierwszy etap refaktoru architektury VetClinic w kierunku systemu rozproszonego BFT. Etap nie implementuje jeszcze pełnych protokolow Narwhal, HotStuff ani SWIM. Celem jest rozdzielenie odpowiedzialnosci i przygotowanie stabilnych kontraktow pod kolejne prace.

## Warstwa domenowa VetClinic

Warstwa domenowa pozostaje odpowiedzialna za logike kliniki weterynaryjnej:

- modele SQLAlchemy i Pydantic dla uzytkownikow, zwierzat, wizyt, faktur i dokumentacji medycznej;
- operacje CRUD i serwisy aplikacyjne;
- istniejace endpointy FastAPI domeny;
- dotychczasowy prosty blockchain i mempool uzywany przez obecne endpointy `/tx/*` oraz `/chain/*`.

Ta warstwa nie powinna znac szczegolow Narwhal, HotStuff ani SWIM. W kolejnych etapach operacje domenowe powinny byc przekazywane do warstwy BFT przez jawny kontrakt, a nie przez bezposrednie zaleznosci od implementacji protokolow.

## Warstwa BFT

Nowy pakiet `vetclinic_api.bft` wyznacza granice architektury odpornej na bledy bizantyjskie:

- `common/types.py` definiuje wspolne enumy i typ `NodeId`;
- `common/events.py` udostepnia `ProtocolEvent` oraz prosty `EventLog`;
- `common/quorum.py` centralizuje obliczenia `f = floor((n - 1) / 3)` i quorum `2f + 1`;
- `narwhal`, `hotstuff`, `swim`, `checkpointing`, `recovery`, `crypto`, `fault_injection`, `observability` sa na razie granicami modulow.

Warstwa BFT ma odpowiadac za przyjmowanie operacji do replikacji, tworzenie batchy, dostepnosc danych, konsensus, wykrywanie awarii, checkpointy, odtwarzanie stanu i metryki protokolow.

## Warstwa przeplywu operacji

Drugi etap refaktoru dodaje pamieciowy przeplyw operacji klienta nad istniejacym projektem. Nie zastapil on jeszcze starego blockchaina ani endpointow RPC. Jego celem jest pokazanie kontraktu BFT, ktory w kolejnych etapach zostanie spiety z Narwhal, HotStuff, SWIM i wykonaniem domenowym.

```text
Client -> /bft/client/submit
       -> Narwhal: BATCHED, AVAILABLE
       -> HotStuff: PROPOSED, VOTED, QC_FORMED, COMMITTED
       -> State Machine: EXECUTED
```

`common/operations.py` przechowuje operacje w `InMemoryOperationStore`, waliduje kolejnosc statusow i udostepnia trace. Kazde przejscie dodaje tez `ProtocolEvent` do `EventLog`, dzieki czemu API moze pokazac zarowno stan operacji, jak i chronologie protokolowa.

Dozwolony przeplyw podstawowy:

```text
RECEIVED -> BATCHED -> AVAILABLE -> PROPOSED -> VOTED -> QC_FORMED -> COMMITTED -> EXECUTED
```

Przed `EXECUTED` operacja moze przejsc w `FAILED` albo `REJECTED`. Po `EXECUTED` stan jest terminalny.

## Warstwa Narwhal

Narwhal odpowiada w tym etapie za lokalne batchowanie operacji, zapis batchy w prostym DAG, ACK dostepnosci danych oraz tworzenie `BatchCertificate`. Nie ma jeszcze prawdziwego broadcastu sieciowego ani podpisow.

```text
ClientOperation(RECEIVED)
   -> NarwhalBatch(BATCHED)
   -> BatchAck
   -> BatchCertificate
   -> DAG vertex
   -> OperationStatus.AVAILABLE
   -> HotStuff proposal input
```

Wierzcholek DAG zawiera batch, opcjonalny certyfikat, ACK node ids i dzieci. Nowy batch wskazuje aktualne tips jako parentow. Po dodaniu batcha tips aktualizuja sie do nowego batcha, a parentom dopisywane sa children.

`BatchCertificate` powstaje po zebraniu quorum zaakceptowanych ACK. Certyfikat oznacza, ze dane batcha sa dostepne dla dalszej warstwy konsensusu. W kolejnym etapie HotStuff nie powinien proponowac pojedynczych operacji, tylko certyfikowane batche.

## Warstwa HotStuff

HotStuff odpowiada za lokalny kontrakt proposal, vote, quorum certificate, commit oraz podstawowy pacemaker/view-change. Nie implementuje jeszcze pelnego sieciowego broadcastu, podpisow ani integracji z wykonaniem domenowym.

```text
BatchCertificate
   -> Proposal
   -> Vote
   -> QuorumCertificate
   -> CommitCertificate
   -> OperationStatus.COMMITTED
```

Proposal moze powstac tylko dla batcha Narwhal z certyfikatem `available=true`. Pierwszy zaakceptowany glos przenosi operacje z `PROPOSED` do `VOTED`. Po quorum glosow powstaje `QuorumCertificate`, ktory przenosi operacje do `QC_FORMED`. Commit bloku wymaga istniejacego QC i przenosi operacje do `COMMITTED`.

Pacemaker jest uproszczony: lider widoku liczony jest jako `(view % total_nodes) + 1`, a `view-change-demo` lokalnie generuje timeout votes do quorum i zwieksza view.

## Warstwa SWIM

SWIM utrzymuje lokalny membership BFT i statusy wezlow. W obecnym etapie nie wykonuje prawdziwych okresowych probingow HTTP; endpointy symuluja ping, ping-req i gossip.

```text
Member(ALIVE)
   -> missed direct ping
   -> SUSPECT
   -> failed indirect ping-req
   -> DEAD
   -> rejoin/recovery
   -> RECOVERING
   -> ALIVE
```

Membership jest integrowany z HotStuff minimalnie: wezel `DEAD` albo `SUSPECT` nie moze byc proposerem ani voterem. `RECOVERING` rowniez nie jest traktowany jako eligible do konsensusu w tej wersji. SWIM nie zmienia jeszcze leader election ani nie oblicza quorum; quorum pozostaje regulem BFT `2f + 1`.

## Warstwa API

FastAPI pozostaje zewnetrznym kontraktem systemu. Istniejace endpointy nie zostaly usuniete ani przepiete.

Nowy router `vetclinic_api.routers.bft` udostepnia:

- `GET /bft/architecture` - opis aktualnego etapu i granic;
- `GET /bft/protocols` - lista planowanych protokolow i modulow;
- `GET /bft/quorum` - obliczenia BFT quorum dla konfiguracji `self + peers`;
- `POST /bft/client/submit` - przyjecie operacji klienta do przeplywu BFT;
- `GET /bft/operations` - lista operacji;
- `GET /bft/operations/{operation_id}` - szczegoly operacji;
- `GET /bft/operations/{operation_id}/trace` - trace statusow operacji;
- `POST /bft/operations/{operation_id}/run-demo` - pelny demonstracyjny przeplyw BFT;
- `GET /bft/events` - odczyt zdarzen protokolow;
- `DELETE /bft/events` - wyczyszczenie pamieciowego logu zdarzen.

Router nie uruchamia jeszcze realnych protokolow. Jest stabilnym kontraktem diagnostycznym i punktem zaczepienia dla kolejnych etapow.

## Monitoring

Projekt ma juz Prometheus i Grafane. Obecne metryki dotycza m.in. API i blockchaina. Docelowo modul `bft/observability` powinien dodac metryki dla:

- liczby operacji w statusach `RECEIVED`, `BATCHED`, `COMMITTED`, `FAILED`;
- czasu tworzenia batchy i certyfikatow quorum;
- widokow HotStuff i zmian lidera;
- statusow SWIM `ALIVE`, `SUSPECT`, `DEAD`, `RECOVERING`;
- checkpointow i transferow stanu.

## Checkpointing i Recovery

Checkpointing tworzy deterministyczny snapshot operacji, ktore sa juz `COMMITTED` albo `EXECUTED`. Snapshot zawiera uporzadkowana liste operacji i hash stanu. `CheckpointCertificate` powstaje po quorum signerow `2f + 1` i staje sie punktem startowym state transfer.

```text
COMMITTED operations
   -> deterministic state snapshot
   -> checkpoint hash
   -> checkpoint certificate
   -> node crash / stale state
   -> state transfer request
   -> apply checkpoint
   -> replay committed operations after checkpoint
   -> RECOVERED / ALIVE
```

Recovery oznacza node jako `RECOVERING`, buduje odpowiedz state transfer z checkpointu, stosuje snapshot i liste operacji po checkpointcie, a na koncu przywraca node do `ALIVE`. Obecna wersja jest lokalna i pamieciowa; prawdziwy transfer sieciowy oraz podpisy certyfikatow sa zostawione na kolejne etapy.

## Warstwa bezpieczenstwa komunikatow

Warstwa `bft/crypto` podpisuje komunikaty protokolow BFT przez Ed25519 i wspolny envelope. Nie konfiguruje jeszcze realnego mTLS, ale przygotowuje kontrakt dla bezpiecznego transportu.

```text
Protocol payload
   -> canonical JSON
   -> nonce
   -> message_id
   -> Ed25519 signature
   -> verify public key
   -> replay check
   -> protocol handler
```

`message_id` jest hashem canonical material z payloadem i nonce. Podpis obejmuje ten sam material, a replay protection uzywa wspolnego `ReplayGuard`. Narwhal, HotStuff, SWIM, Checkpointing i Recovery dodaja `signed_message_id` do zdarzen diagnostycznych.

## Observability i demonstracja

Observability spina zdarzenia protokolow z metrykami, health checkami i raportem demo. Testy dzialaja bez Prometheus/Grafana, ale endpoint metryk eksportuje format Prometheus.

```text
ProtocolEvent
   -> EventLog
   -> BftMetrics
   -> HealthService
   -> DemoReport
   -> Prometheus/Grafana
```

`BftDemoScenarioRunner` wykonuje lokalny scenariusz koncowy: crypto keys, SWIM bootstrap, operacja BFT, Narwhal, HotStuff, execute, fault injection, checkpoint, recovery i crypto replay detection.

## Fault Injection

Istniejace mechanizmy w `middleware/chaos.py` i `admin/network_state.py` symuluja opoznienia, bledy, offline, flapping i odrzucanie RPC. Modul `bft/fault_injection` dodaje osobna, protokolowa warstwe BFT dla lokalnych testow i demonstracji:

- crash;
- delay;
- drop;
- duplicate;
- replay;
- equivocation;
- network partition;
- leader failure;
- state corruption.

Reguly fault injection sa oceniane przy komunikatach Narwhal (`BATCH`, `BATCH_ACK`), HotStuff (`PROPOSAL`, `VOTE`, `COMMIT`) i SWIM (`SWIM_PING`, `SWIM_ACK`, `SWIM_GOSSIP`). Partycje sieciowe blokuja komunikacje miedzy grupami node'ow, replay jest wykrywany przez `ReplayGuard`, a equivocation przez `EquivocationDetector`.

Obecny etap nie zmienia starszych mechanizmow, zeby nie naruszyc istniejacych skryptow.

## Przyszle moduly Narwhal, HotStuff i SWIM

Narwhal powinien przejac batchowanie operacji, tworzenie DAG i zapewnienie data availability. Nie powinien wykonywac logiki domenowej VetClinic.

HotStuff powinien odpowiadac za proposal, vote, quorum certificate, commit i view-change. Powinien konsumowac dostepne dane z warstwy Narwhal i finalizowac operacje w kolejnosci wykonania.

SWIM powinien utrzymywac membership i statusy wezlow. Jego wynik powinien zasilac decyzje operacyjne, ale nie moze samodzielnie zastapic konsensusu BFT.

## Granice odpowiedzialnosci

- Domena VetClinic definiuje operacje biznesowe i stan aplikacji.
- BFT replikuje operacje, ustala ich kolejnosc, obsluguje awarie i recovery.
- API wystawia kontrakty HTTP dla klientow, operatorow i demonstracji.
- Monitoring obserwuje system bez wplywania na decyzje protokolow.
- Fault injection symuluje awarie w kontrolowany sposob, bez mieszania sie z logika domenowa.

Najwazniejsza zasada kolejnych etapow: implementacje protokolow nie powinny importowac routerow ani CRUD VetClinic. Integracja powinna isc przez male kontrakty operacji, zdarzen i wykonania stanu.
