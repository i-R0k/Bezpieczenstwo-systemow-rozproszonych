# gRPC i protobuf

Harmonogram projektu obejmowal przygotowanie komunikacji gRPC oraz definicji `.proto` dla wymiany komunikatow miedzy wezlami.

Aktualny poziom implementacji to `contract + local demo runtime`. Podstawowa sciezka wykonania projektu nadal pozostaje oparta o FastAPI/HTTP, endpointy `/bft/*` i serwisy in-memory, ale repo zawiera tez dzialajacy lokalny runtime gRPC dla jednego przeplywu SWIM.

## Kontrakt protobuf

Plik `proto/bft.proto` opisuje docelowy kontrakt node-to-node:

- podpisana koperta `BftEnvelope`;
- Narwhal batch i ACK;
- HotStuff proposal i vote;
- SWIM ping/ack/gossip;
- state transfer request/response;
- serwis `BftNodeService`.

Serwis zawiera metody:

- `SendBatch`;
- `SendBatchAck`;
- `SendProposal`;
- `SendVote`;
- `SendSwimPing`;
- `SendSwimGossip`;
- `SendStateTransferRequest`;
- `SendStateTransferResponse`.

## Runtime demo

Pakiet `vetclinic_api.bft.grpc_runtime` zawiera:

- `compiler.py` - dynamiczna kompilacja `proto/bft.proto` przez `grpc_tools.protoc` do katalogu tymczasowego;
- `server.py` - lokalny gRPC server demo;
- `client.py` - lokalny klient gRPC;
- `models.py` - modele odpowiedzi API.

Dzialajacy runtime demo obejmuje metode `SendSwimPing`. Serwer zapisuje w `EventLog` zdarzenie `grpc_swim_ping_received` z `transport="grpc"` i zwraca `SwimAckMessage` ze statusem `ALIVE`.

Pozostale metody zwracaja `Ack(accepted=false, reason="not_implemented_in_demo_runtime")`, poniewaz pelny transport Narwhal/HotStuff/recovery po gRPC nie jest celem tego etapu.

## Endpointy

```text
GET  /bft/grpc/contract
GET  /bft/grpc/runtime/status
POST /bft/grpc/runtime/ping-demo
```

`POST /bft/grpc/runtime/ping-demo` startuje lokalny serwer na `127.0.0.1:0`, wykonuje klientem `SendSwimPing`, zatrzymuje serwer w `finally` i zwraca wynik ACK. Nie wymaga Dockera ani zewnetrznego portu.

## Testy

```powershell
python -m pytest tests/bft/test_101_grpc_contract.py -q
python -m pytest tests/bft/test_104_grpc_runtime_demo.py -q
python -m pytest tests/security/test_21_grpc_runtime_security.py -q
```

## Ograniczenia

- Runtime demo uzywa lokalnego insecure channel.
- mTLS dla gRPC nie jest aktywne w tym runtime; jest opisane osobno w `docs/MTLS.md`.
- Tylko `SendSwimPing` ma dzialajacy runtime.
- Pelny Narwhal, HotStuff i StateTransfer po gRPC pozostaja rozszerzeniem.
- Podstawowy testbed BFT nadal dziala przez FastAPI/in-memory.
