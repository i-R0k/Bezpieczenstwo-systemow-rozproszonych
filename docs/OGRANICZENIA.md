# Ograniczenia implementacji

Projekt jest demonstracyjna i edukacyjna implementacja warstwy BFT oraz testow bezpieczenstwa. Ograniczenia sa czescia jawnego zakresu projektu, a nie ukrytymi zalozeniami.

## gRPC

- `proto/bft.proto` definiuje kontrakt docelowej komunikacji node-to-node.
- Endpoint `/bft/grpc/contract` potwierdza kontrakt, a `/bft/grpc/runtime/ping-demo` uruchamia lokalny runtime demo dla `SendSwimPing`.
- Runtime demo uzywa lokalnego insecure channel i dynamicznie generowanych stubow.
- Pelny transport Narwhal/HotStuff/state transfer po gRPC nie jest aktywny.
- Podstawowy testbed pozostaje oparty o FastAPI, serwisy in-memory i pytest.

## mTLS

- Runtime domyslny nie wymusza mTLS.
- Endpoint `/bft/security/transport` zwraca `mtls_runtime_enabled=false`.
- `scripts/generate_demo_certs.py` generuje certyfikaty demo, a `docker-compose.override.tls.example.yml` pokazuje przyklad TLS.
- Produkcyjna konfiguracja mTLS wymagalaby proxy typu Envoy/nginx/Traefik albo gRPC TLS credentials oraz zarzadzania zaufaniem certyfikatow.

## 2FA

- 2FA/TOTP jest minimalnym flow demonstracyjnym.
- Sekrety sa przechowywane in-memory w `TOTP_DEMO_STORE`.
- Brakuje pelnego enrollmentu uzytkownika, QR rendering, recovery codes, resetu 2FA i audytu logowania.
- Endpoint `/bft/client/submit-secure-demo` wymaga poprawnego TOTP tylko w strict mode.

## GUI/dashboard

- `/bft/dashboard` jest statycznym HTML dashboardem bez React/Vue.
- Dashboard uzywa polling/fetch, bez WebSocket i bez push events.
- `/bft/communication/log` pokazuje logiczny log zdarzen z `EventLog`.
- To nie jest packet capture ani wizualizacja prawdziwego ruchu sieciowego.

## Komunikacja miedzy procesami

- Wezly BFT sa modelowane logicznie przez `node_id`.
- Testbed nie uruchamia osobnych procesow BFT ani prawdziwego transportu node-to-node.
- Docker Compose zawiera bazowe serwisy projektu, ale nie jest wymagany przez BFT/security/pentest tests.
- Partycje, dropy i awarie dzialaja na poziomie lokalnych kontraktow service/router.

## Trwalosc stanu

- Stan BFT jest in-memory.
- DAG Narwhal, QC/commity HotStuff, SWIM membership, checkpointy, recovery, replay guard i klucze demo znikaja po restarcie procesu.
- Brak trwalej bazy danych dla BFT state.

## Paper-grade Narwhal/HotStuff/SWIM

- Narwhal, HotStuff i SWIM sa implementacjami demonstracyjnymi, nie pelnymi implementacjami paper-grade.
- Narwhal nie wykonuje rozproszonego broadcastu data availability.
- HotStuff nie zawiera produkcyjnego pacemakera, pipeliningu wielu widokow ani rzeczywistego broadcastu glosow.
- SWIM modeluje membership i failure detection lokalnie, bez pelnego losowego gossipu w sieci.

## Security i pentest

- Strict mode jest demonstracyjnym hardeningiem administracyjnych endpointow, nie pelnym IAM.
- Pentest harness jest lokalny i ograniczony do `localhost`/`127.0.0.1`.
- ZAP, Nuclei i ffuf sa opcjonalne; brak narzedzia skutkuje statusem `skipped`, a nie awaria podstawowych testow.
- Raporty security/pentest sa generowane lokalnie do `reports/` albo `pentest/reports/` i sa ignorowane przez git poza plikami `.gitkeep`.
- `certs/demo` sluzy do lokalnego generowania prywatnych kluczy i certyfikatow demo; te pliki nie powinny byc commitowane.
