# Demo koncowe BFT

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
