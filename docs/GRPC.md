# gRPC i protobuf

Harmonogram projektu obejmowal przygotowanie komunikacji gRPC oraz definicji `.proto` dla wymiany komunikatow miedzy wezlami.

Aktualny testbed pozostaje oparty o FastAPI/HTTP, endpointy `/bft/*` i serwisy in-memory. To jest podstawowa sciezka wykonania uzywana przez testy `tests/bft`, `tests/security` i `tests/pentest`.

## Kontrakt protobuf

Plik `proto/bft.proto` opisuje docelowy kontrakt node-to-node:

- podpisana koperta `BftEnvelope`;
- Narwhal batch i ACK;
- HotStuff proposal i vote;
- SWIM ping/ack/gossip;
- state transfer request/response;
- serwis `BftNodeService`.

## Poziom implementacji

Poziom implementacji to `contract-only`. Oznacza to, ze repo zawiera stabilny kontrakt `.proto`, dokumentacje i helpery mapowania w `vetclinic_api.bft.grpc_contract`, ale nie uruchamia jeszcze pelnego runtime gRPC.

Pelny runtime gRPC, generowanie klas protobuf, transport miedzy osobnymi procesami oraz integracja z Docker Compose sa rozszerzeniem rozwojowym. Nie sa wymagane do obecnej demonstracji.
