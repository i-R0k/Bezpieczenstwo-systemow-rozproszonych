# gRPC contract mapping

Ten pakiet zawiera lekkie helpery mapujace obecne modele BFT na ksztalt kontraktu `proto/bft.proto`.

Nie zalezy od wygenerowanych klas protobuf i nie uruchamia serwera gRPC. Celem jest utrzymanie jawnego kontraktu transportowego dla przyszlej komunikacji node-to-node przy zachowaniu obecnej sciezki FastAPI/in-memory jako podstawowego testbedu.
