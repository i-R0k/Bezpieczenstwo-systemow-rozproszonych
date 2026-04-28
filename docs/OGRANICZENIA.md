# Ograniczenia implementacji

Projekt jest demonstracyjna implementacja edukacyjna warstwy BFT, przygotowana do prezentacji i analizy. Ponizsze ograniczenia sa swiadomym zakresem projektu, a nie ukrytymi bledami.

## Stan i trwalosc

- Implementacja BFT dziala in-memory.
- Nie ma trwalej bazy danych dla BFT state, DAG, QC, checkpointow ani recovery.
- Restart procesu API czysci stan demonstracyjny.

## Siec i procesy

- Testbed nie uruchamia prawdziwej sieci BFT miedzy osobnymi procesami.
- Wezly sa modelowane logicznie przez `node_id`.
- Docker Compose nadal zawiera bazowe serwisy projektu VetClinic i nie jest glowna sciezka testbedu BFT.

## Protokoly

- Narwhal, HotStuff i SWIM sa implementacjami demonstracyjnymi, nie pelnymi implementacjami paper-grade.
- Narwhal nie wykonuje rzeczywistego broadcastu data availability miedzy procesami.
- HotStuff formuje QC i commit lokalnie, bez produkcyjnego transportu i pipeline wielu widokow.
- SWIM modeluje failure detection lokalnie, bez pelnego losowego gossipu w rozproszonej sieci.

## Fault injection

- Fault injection jest lokalny i deterministyczny.
- `DELAY` w testach nie wykonuje realnych `sleep`, tylko zapisuje decyzje o opoznieniu.
- Partycje i dropy blokuja lokalna sciezke service/router, nie prawdziwy interfejs sieciowy.

## Bezpieczenstwo

- Klucze demo sa in-memory.
- Replay protection dziala w pamieci procesu.
- mTLS nie jest produkcyjnie skonfigurowane.
- Ed25519 i canonical JSON pokazuja kontrakt podpisanych komunikatow, ale nie zastepuja kompletnej infrastruktury kluczy.

## GUI i monitoring

- GUI nie jest glowna sciezka demonstracyjna BFT.
- Prometheus/Grafana moga byc uzyte pomocniczo, ale testbed BFT nie wymaga ich uruchomienia.
- Podstawowa demonstracja odbywa sie przez `scripts/run_bft_testbed.py`, Swagger UI i endpointy `/bft/*`.
