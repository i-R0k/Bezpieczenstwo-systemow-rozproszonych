# Observability BFT

## Cel

Warstwa `bft/observability` zbiera zdarzenia protokolow BFT do metryk Prometheus, udostepnia health check komponentow i uruchamia automatyczny scenariusz demonstracyjny bez Dockera, uvicorn i prawdziwej sieci.

## Metryki

Counters obejmuja m.in. operacje submitted/executed, Narwhal batches/certificates, HotStuff proposals/votes/QC/commits/view changes, SWIM ping/suspect/dead, faults/replay/equivocation, checkpoints/recoveries oraz crypto signed/verified/rejected.

Gauges obejmuja rozmiar operation store, liczbe wierzcholkow DAG, aktualny view HotStuff, statusy SWIM, aktywne fault rules, checkpointy, recovery states i public keys.

Histograms sa przygotowane dla end-to-end operation, checkpoint creation i recovery duration.

## Endpointy

- `GET /bft/observability/health`
- `GET /bft/observability/metrics`
- `GET /bft/observability/metrics/snapshot`
- `POST /bft/demo/run`
- `GET /bft/demo/last-report`
- `DELETE /bft/demo/last-report`

## Demo Report

`POST /bft/demo/run` wykonuje lokalnie:

1. Bootstrap SWIM i demo crypto keys.
2. Submit operation.
3. Narwhal batch/certificate.
4. HotStuff proposal/QC/commit.
5. Execute.
6. Fault injection.
7. Checkpoint.
8. Recovery node3.
9. Crypto verification i replay detection.
10. Health after i metrics snapshot.

## Uruchamianie

```powershell
python scripts/run_bft_testbed.py
make test-bft-observability
```

## Prometheus i Grafana

Testy nie wymagaja Prometheus/Grafana. Ręcznie mozna uruchomic stack przez:

```powershell
docker compose up --build
```

Istniejacy Prometheus scrapuje endpoint `/metrics`. Endpoint `/bft/observability/metrics` eksportuje metryki BFT w formacie Prometheus i moze byc dodany jako osobny scrape target albo wykorzystany diagnostycznie.

Proponowane panele Grafana:

- operations submitted/executed;
- Narwhal batches/certificates;
- HotStuff proposals/QC/commits/view changes;
- SWIM alive/suspect/dead;
- faults/replay/equivocation;
- checkpoints/recoveries;
- crypto verified/rejected.

## Ograniczenia

- Metryki BFT sa lokalne i in-memory.
- Testy nie uruchamiaja Dockera.
- Dashboard BFT jest opisany dokumentacyjnie; istniejace dashboardy legacy zostaja bez zmian.
