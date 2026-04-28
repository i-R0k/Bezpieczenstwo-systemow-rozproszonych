# Narwhal

Ten dokument opisuje lokalna warstwe Narwhal dodana w trzecim etapie refaktoru. Implementacja jest modelem demonstracyjnym batchowania, DAG i data availability. Nie jest jeszcze pelnym protokolem sieciowym.

## Cel modulu

Narwhal oddziela przyjmowanie operacji od konsensusu HotStuff. Jego zadania w obecnym etapie:

- pobrac operacje ze statusem `RECEIVED`;
- utworzyc `NarwhalBatch`;
- zapisac batch jako wierzcholek lokalnego DAG;
- zarejestrowac ACK dostepnosci danych;
- utworzyc `BatchCertificate` po quorum;
- oznaczyc operacje jako `BATCHED`, a po certyfikacji jako `AVAILABLE`.

## Modele

- `NarwhalBatch` - batch operacji z `batch_id`, autorem, runda, parentami i `payload_hash`.
- `BatchAck` - lokalne potwierdzenie dostepnosci batcha przez wezel.
- `BatchCertificate` - wynik quorum ACK dla batcha.
- `DagVertex` - wierzcholek DAG z batchem, certyfikatem, ACK i dziecmi.
- `NarwhalDagView` - diagnostyczny widok DAG.
- `NarwhalBatchRequest` - wejscie API do utworzenia batcha.
- `NarwhalBatchResponse` - odpowiedz z batchem, opcjonalnym certyfikatem i operacjami oznaczonymi jako `BATCHED`.

## Endpointy

- `POST /bft/narwhal/batches` - tworzy batch z podanych operacji albo z maksymalnie `max_operations` operacji `RECEIVED`.
- `GET /bft/narwhal/batches` - lista batchy.
- `GET /bft/narwhal/batches/{batch_id}` - szczegoly batcha.
- `POST /bft/narwhal/batches/{batch_id}/ack` - dodaje ACK.
- `POST /bft/narwhal/batches/{batch_id}/certify-demo` - lokalnie dodaje ACK do quorum.
- `GET /bft/narwhal/batches/{batch_id}/certificate` - pobiera certyfikat.
- `GET /bft/narwhal/dag` - widok DAG.
- `GET /bft/narwhal/tips` - aktualne tips DAG.
- `DELETE /bft/narwhal` - czysci stan Narwhal; opcjonalnie `clear_operations=true` czysci tez operacje.

## Przeplyw

```text
POST /bft/client/submit
  -> ClientOperation(RECEIVED)
POST /bft/narwhal/batches
  -> NarwhalBatch
  -> OperationStatus.BATCHED
POST /bft/narwhal/batches/{batch_id}/ack
  -> BatchAck
POST /bft/narwhal/batches/{batch_id}/certify-demo
  -> BatchCertificate
  -> OperationStatus.AVAILABLE
GET /bft/narwhal/dag
  -> NarwhalDagView
```

`/bft/operations/{operation_id}/run-demo` korzysta teraz z Narwhal do etapow `BATCHED` i `AVAILABLE`, a dopiero pozniej przechodzi przez demonstracyjna czesc HotStuff.

## Ograniczenia aktualnej implementacji

- Stan jest in-memory.
- ACK sa lokalne i nie maja podpisow.
- `certify-demo` symuluje ACK od kolejnych `node_id`.
- Brak broadcastu batchy do peerow.
- Brak walidacji kryptograficznej data availability.
- DAG jest lokalny i prosty: nowy batch wskazuje aktualne tips jako parentow.
- HotStuff nie konsumuje jeszcze realnie `BatchCertificate`.

## Plan rozbudowy do broadcastu sieciowego

Kolejny krok Narwhal powinien dodac:

- endpoint odbioru batcha od peerow;
- podpisane `BatchAck`;
- broadcast batcha do `CONFIG.peers`;
- retransmisje i timeouty;
- walidacje parentow zdalnych batchy;
- oddzielenie lokalnego autora batcha od walidatorow;
- metryki czasu certyfikacji i liczby ACK;
- przekazanie `BatchCertificate` jako formalnego wejscia do HotStuff proposal.
