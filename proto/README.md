# BFT protobuf contract

`proto/bft.proto` opisuje docelowy kontrakt komunikacji node-to-node dla demonstratora BFT.

Obecna sciezka wykonania projektu pozostaje oparta o FastAPI, endpointy `/bft/*` oraz serwisy in-memory. Plik `.proto` nie jest obecnie generowany do kodu produkcyjnego i nie uruchamia pelnego gRPC runtime.

Kontrakt obejmuje komunikaty Narwhal, HotStuff, SWIM, state transfer oraz podpisana koperte `BftEnvelope`, zgodna z warstwa crypto/replay protection.
