# Demo koncowe BFT

## Dashboard BFT i reset demo chain

Dla 6-wezlowego klastra Docker ustaw PyQt BFT Dashboard na hostowy adres
`http://127.0.0.1:8001` (Docker `node1`). Standalone API na
`http://127.0.0.1:8000` nie ma zmiennej `PEERS`, wiec poprawnie raportuje jeden
skonfigurowany wezel i dashboard pokazuje diagnostyke standalone/no-peers
zamiast udawac klaster. Domyslny target startowy mozna nadpisac przez
`BFT_DASHBOARD_BASE_URL`.

Przed diagnoza wysokosci lancucha albo podpisow zatrzymaj ruch, zeby reset nie
zostal natychmiast zaklocony:

```bash
docker compose stop trafficgen
# albo
curl -X PUT http://127.0.0.1:8001/admin/network/sim \
  -H "Content-Type: application/json" \
  -d '{"traffic_enabled":false}'
```

Reset klastra uruchamiaj z node1:

```bash
curl -X POST "http://127.0.0.1:8001/admin/network/reset-demo-chain?scope=cluster"
```

Odpowiedz zawiera wynik per node z `height` i `verification_status`. Po czystym
resecie node1..node6 powinny miec `height=0` i `verification_status=VALID`.

## Scenariusze uzycia z harmonogramu w GUI

Te dwa przebiegi sa jawnie dostepne w PyQt BFT Dashboard w zakladce
`Demo actions`.

### Scenario 1 - poprawne uruchomienie klastra i dashboardu

Mozliwe wykorzystanie przez usera: prowadzacy albo operator demo chce szybko
sprawdzic, czy GUI jest podlaczone do prawdziwego klastra Docker, a nie do
standalone API.

Kroki:

1. Uruchom `docker compose up -d node1 node2 node3 node4 node5 node6`.
2. Uruchom GUI z `--base-url http://127.0.0.1:8001`.
3. W `Demo actions` kliknij `S1: Cluster`.

Oczekiwany wynik testowy:

```text
configured_total_nodes = 6
chain verification_status = VALID
dashboard target = http://127.0.0.1:8001
passed = True
```

### Scenario 2 - pelny przebieg operacji klienta przez BFT

Mozliwe wykorzystanie przez usera: prowadzacy chce odtworzyc caly przebieg
klienta przez BFT bez recznego klikania endpointow Narwhal, HotStuff,
checkpointingu i recovery.

Kroki:

1. W `Demo actions` kliknij `S2: Full BFT`.
2. GUI najpierw czysci faults, potem uruchamia pelny demo flow i pobiera raport.
3. Pokaz `Overview`, `Protocols` i `Live logs`.

Oczekiwany wynik testowy:

```text
final_operation_status = EXECUTED
checkpoint_id = present
recovered_node_id = 3
steps contain Submit operation, Narwhal, HotStuff, Execute, Checkpoint, Recovery
passed = True
```

### Scenario 3 - logical processes

Mozliwe wykorzystanie przez usera: prowadzacy chce pokazac procesy logiczne
bez recznego laczenia danych z raportu, event logu i communication logu.

Kroki:

1. W `Demo actions` kliknij `S3: BFT logic`.
2. GUI czysci faults, uruchamia pelny demo flow i pobiera eventy oraz communication log.
3. W oknie JSON pokaz `logical_processes`.
4. Przejdz do `Live logs`, zeby pokazac te same zdarzenia jako log protokolow.

Oczekiwany wynik testowy:

```text
logical_processes contain Client/API, Narwhal availability, HotStuff consensus,
State machine execution, Checkpointing, Recovery/state transfer
final_operation_status = EXECUTED
passed = True
```

### Scenario 4 - recovery logical process

Mozliwe wykorzystanie przez usera: prowadzacy chce pokazac drugi proces
logiczny zwiazany z awaria wezla, recovery gate i powrotem do klastra.

Kroki:

1. W `Demo actions` kliknij `S4: Recovery logic`.
2. GUI uruchamia pelny demo flow, zeby miec checkpoint/recovery context.
3. GUI ustawia node2 kolejno jako `DEAD`, `RECOVERING` i `ALIVE`.
4. W oknie JSON pokaz `logical_processes` oraz aktualny `swim_status`.

Oczekiwany wynik testowy:

```text
logical_processes contain Failure detection, Recovery gate, Membership rejoin,
Cluster view
node2 status sequence = DEAD -> RECOVERING -> ALIVE
passed = True
```

## Automatyczny scenariusz API

```powershell
curl.exe -X POST http://localhost:8001/bft/demo/run
curl.exe http://localhost:8001/bft/demo/last-report
```

Oczekiwany wynik: `BftDemoReport.status == "ok"`, operacja konczy jako `EXECUTED`, checkpoint ma `checkpoint_id`, a node3 zostaje odzyskany jako `RECOVERED` i `ALIVE`.

## Scenariusz CLI przez testbed

```powershell
python scripts/run_bft_testbed.py
make test-bft-observability
```

Testbed nie wymaga Dockera ani prawdziwej sieci.

## Scenariusz reczny

1. `POST /bft/crypto/demo-keys`
2. `POST /bft/swim/bootstrap`
3. `POST /bft/client/submit`
4. `POST /bft/operations/{operation_id}/run-demo`
5. `POST /bft/checkpointing/snapshots`
6. `POST /bft/checkpointing/snapshots/{snapshot_id}/certify`
7. `POST /bft/recovery/nodes/3/recover-demo`
8. `GET /bft/observability/health`
9. `GET /bft/observability/metrics`

## Przykladowy raport

```json
{
  "status": "ok",
  "final_operation_status": "EXECUTED",
  "checkpoint_id": "sha256...",
  "recovered_node_id": 3,
  "errors": []
}
```

## Co pokazac prowadzacemu

- Pelny flow Narwhal -> HotStuff -> execute.
- Fault injection zmieniajacy status SWIM.
- Checkpoint i recovery node3.
- Crypto replay detection.
- Health endpoint i metryki BFT.
- Testbed `58+` testow przechodzacy bez Dockera.
