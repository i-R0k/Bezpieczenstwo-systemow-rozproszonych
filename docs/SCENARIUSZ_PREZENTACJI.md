# Scenariusz prezentacji

Ten przebieg miesci sie w 10-15 minutach. Najpierw pokazuje automatyczny testbed, potem ten sam zakres przez API.

## Scenariusz 1: testbed automatyczny

Cel: pokazac, ze repo ma powtarzalny testbed bez Dockera.

Komenda:

```powershell
python scripts/run_bft_testbed.py
```

Oczekiwany wynik: runner wypisuje sekcje testow, pytest konczy sie wynikiem pozytywnym.

Co powiedziec prowadzacemu: testbed sprawdza kontrakty Narwhal, HotStuff, SWIM, fault injection, checkpointing, recovery, crypto, observability, final demo i dokumentacje.

## Scenariusz 2: demo API

Cel: pokazac finalny happy path przez endpoint.

Komendy albo endpointy:

```powershell
$env:PYTHONPATH="VetClinic/API"
python -m uvicorn vetclinic_api.main:app --host 127.0.0.1 --port 8001 --reload
curl.exe -X POST http://127.0.0.1:8001/bft/demo/run
curl.exe http://127.0.0.1:8001/bft/demo/last-report
```

Oczekiwany wynik: `status` ma wartosc `ok`, operacja konczy jako `EXECUTED`, raport ma `checkpoint_id`, `recovered_node_id` i `metrics_snapshot`.

Co powiedziec prowadzacemu: jeden endpoint uruchamia pelna demonstracje protokolow i zapisuje raport do pozniejszego odczytu.

## Scenariusz 3: Narwhal

Cel: pokazac batch, certyfikat data availability i DAG.

Endpointy:

```text
POST /bft/client/submit
POST /bft/narwhal/batches
POST /bft/narwhal/batches/{batch_id}/certify-demo
GET  /bft/narwhal/dag
```

Oczekiwany wynik: operacja przechodzi z `RECEIVED` do `BATCHED` i `AVAILABLE`, a DAG zawiera batch jako wierzcholek.

Co powiedziec prowadzacemu: Narwhal oddziela dostepnosc danych od konsensusu; w projekcie jest to lokalny, in-memory kontrakt demonstracyjny.

## Scenariusz 4: HotStuff

Cel: pokazac proposal, QC i commit.

Endpointy:

```text
POST /bft/hotstuff/proposals
POST /bft/hotstuff/proposals/{proposal_id}/form-qc-demo
POST /bft/hotstuff/qc/{qc_id}/commit
GET  /bft/hotstuff/status
```

Oczekiwany wynik: powstaje proposal, quorum certificate i commit certificate.

Co powiedziec prowadzacemu: HotStuff konsumuje certyfikowany batch Narwhal i tworzy logiczne zatwierdzenie operacji.

## Scenariusz 5: SWIM

Cel: pokazac membership i failure detection.

Endpointy:

```text
POST /bft/swim/bootstrap
POST /bft/swim/ping/{target_node_id}?simulate_success=false
POST /bft/swim/probe-demo/{target_node_id}
PUT  /bft/swim/members/{node_id}/dead
GET  /bft/swim/status
```

Oczekiwany wynik: wezel zmienia status na `SUSPECT` albo `DEAD`.

Co powiedziec prowadzacemu: status czlonka klastra jest uzywany przez HotStuff do odrzucania niepoprawnych glosujacych albo proposerow.

## Scenariusz 6: fault injection

Cel: pokazac kontrolowane awarie komunikatow.

Endpointy:

```text
POST /bft/faults/rules
POST /bft/faults/evaluate
GET  /bft/faults/status
DELETE /bft/faults
```

Przyklad reguly: `DROP` dla `HOTSTUFF` i `VOTE`.

Oczekiwany wynik: `FaultDecision` pokazuje zablokowany komunikat.

Co powiedziec prowadzacemu: testy nie czekaja realnie na opoznienia; fault injection jest deterministyczny i szybki.

## Scenariusz 7: checkpoint/recovery

Cel: pokazac snapshot, state transfer i powrot wezla.

Endpointy:

```text
POST /bft/checkpointing/snapshots
POST /bft/checkpointing/snapshots/{snapshot_id}/certify
PUT  /bft/swim/members/{node_id}/recovering
POST /bft/recovery/nodes/{node_id}/recover-demo
GET  /bft/recovery/status
```

Oczekiwany wynik: recovery stosuje checkpoint, hash stanu jest zgodny, a wezel wraca do `ALIVE`.

Co powiedziec prowadzacemu: state transfer jest lokalnym modelem edukacyjnym, ale kontrakt obejmuje identyfikator checkpointu i hash stanu.

## Scenariusz 8: crypto/replay

Cel: pokazac podpisy i replay protection.

Endpointy:

```text
POST /bft/crypto/demo-keys
POST /bft/crypto/sign
POST /bft/crypto/verify
POST /bft/crypto/verify
```

Oczekiwany wynik: pierwsza weryfikacja zwraca `valid=true`, druga tego samego komunikatu zwraca `replay=true`.

Co powiedziec prowadzacemu: podpis obejmuje canonical JSON, nonce i body, a replay guard odrzuca ponowne uzycie `message_id`.

## Scenariusz 9: observability

Cel: pokazac stan systemu i metryki.

Endpointy:

```text
GET /bft/observability/health
GET /bft/observability/metrics
GET /bft/observability/metrics/snapshot
GET /bft/demo/last-report
```

Oczekiwany wynik: health nie zwraca 500, metryki sa w formacie Prometheus, raport demo zawiera kroki i snapshot metryk.

Co powiedziec prowadzacemu: obserwowalnosc jest czescia kontraktu projektu i jest testowana automatycznie.
