# API BFT

Ten dokument kataloguje endpointy z prefiksem `/bft`. Przyklady requestow sa minimalne; pelne schematy sa widoczne w Swagger UI pod `/docs`.

Typowe bledy dla calego API: `400` dla niepoprawnych danych, `404` dla brakujacego zasobu, `409` dla konfliktu stanu protokolu, `422` dla niepoprawnego JSON-a wedlug FastAPI.

## Architecture/status

### GET `/bft/architecture`

Opis: zwraca opis granic architektury BFT i stan modulow.

Request: brak.

Response: JSON z opisem `common`, `narwhal`, `hotstuff`, `swim`, `fault_injection`, `checkpointing`, `recovery`, `crypto`, `observability`.

Typowe bledy: brak.

### GET `/bft/protocols`

Opis: zwraca liste protokolow i zakres odpowiedzialnosci.

Request: brak.

Response: lista modulow BFT.

Typowe bledy: brak.

### GET `/bft/quorum`

Opis: zwraca konfiguracje quorum `2f + 1` dla aktualnej liczby wezlow.

Request: brak.

Response: opis `total_nodes`, `fault_tolerance`, `quorum`.

Typowe bledy: brak.

### GET `/bft/events`

Opis: zwraca event log protokolow BFT.

Request: brak.

Response: lista zdarzen.

Typowe bledy: brak.

### DELETE `/bft/events`

Opis: czysci event log.

Request: brak.

Response: liczba usunietych zdarzen.

Typowe bledy: brak.

## Operations

### POST `/bft/client/submit`

Opis: tworzy operacje klienta w statusie `RECEIVED`.

Request:

```json
{"sender":"alice","recipient":"bob","amount":10.5,"payload":{"kind":"demo"}}
```

Response: `ClientOperation` z `operation_id`.

Typowe bledy: `422`.

### GET `/bft/operations`

Opis: lista operacji w pamieci.

Request: brak.

Response: lista `ClientOperation`.

Typowe bledy: brak.

### GET `/bft/operations/{operation_id}`

Opis: szczegoly operacji.

Request: brak.

Response: `ClientOperation`.

Typowe bledy: `404`.

### GET `/bft/operations/{operation_id}/trace`

Opis: trace operacji i przejsc statusow.

Request: brak.

Response: `OperationTrace` z `operation` i `transitions`.

Typowe bledy: `404`.

### POST `/bft/operations/{operation_id}/batch`

Opis: tworzy batch Narwhal dla pojedynczej operacji.

Request: brak.

Response: `NarwhalBatchResponse`.

Typowe bledy: `404`, `409`.

### POST `/bft/operations/{operation_id}/available`

Opis: certyfikuje batch operacji demonstracyjnie.

Request: brak.

Response: `BatchCertificate`.

Typowe bledy: `404`, `409`.

### POST `/bft/operations/{operation_id}/propose`

Opis: tworzy proposal HotStuff dla operacji dostepnej w Narwhal.

Request: brak.

Response: `HotStuffProposal`.

Typowe bledy: `404`, `409`.

### POST `/bft/operations/{operation_id}/vote`

Opis: oddaje glos demonstracyjny na proposal operacji.

Request:

```json
{"voter_node_id":2,"accepted":true}
```

Response: glos HotStuff.

Typowe bledy: `404`, `409`.

### POST `/bft/operations/{operation_id}/form-qc`

Opis: tworzy quorum certificate dla operacji.

Request: brak.

Response: `QuorumCertificate`.

Typowe bledy: `404`, `409`.

### POST `/bft/operations/{operation_id}/commit`

Opis: wykonuje commit operacji.

Request: brak.

Response: `CommitCertificate`.

Typowe bledy: `404`, `409`.

### POST `/bft/operations/{operation_id}/execute`

Opis: oznacza zatwierdzona operacje jako `EXECUTED`.

Request: brak.

Response: `ClientOperation`.

Typowe bledy: `404`, `409`.

### POST `/bft/operations/{operation_id}/run-demo`

Opis: przeprowadza pojedyncza operacje przez demonstracyjny flow.

Request: brak.

Response: `OperationTrace`.

Typowe bledy: `404`, `409`.

### DELETE `/bft/operations`

Opis: czysci operacje.

Request: brak.

Response: liczba usunietych operacji.

Typowe bledy: brak.

## Narwhal

### POST `/bft/narwhal/batches`

Opis: tworzy batch z operacji `RECEIVED` albo z podanych operacji.

Request:

```json
{"max_operations":10}
```

Response: `NarwhalBatchResponse`.

Typowe bledy: `400`, `409`, `422`.

### GET `/bft/narwhal/batches`

Opis: lista batchy.

Request: brak.

Response: lista `NarwhalBatch`.

Typowe bledy: brak.

### GET `/bft/narwhal/batches/{batch_id}`

Opis: szczegoly batcha.

Request: brak.

Response: `NarwhalBatch`.

Typowe bledy: `404`.

### POST `/bft/narwhal/batches/{batch_id}/ack`

Opis: zapisuje ACK data availability od wezla.

Request:

```json
{"node_id":2,"accepted":true}
```

Response: ACK i ewentualny certyfikat.

Typowe bledy: `404`, `409`.

### POST `/bft/narwhal/batches/{batch_id}/certify-demo`

Opis: lokalnie zbiera quorum ACK i certyfikuje batch.

Request: brak.

Response: `BatchCertificate`.

Typowe bledy: `404`, `409`.

### GET `/bft/narwhal/batches/{batch_id}/certificate`

Opis: zwraca certyfikat batcha.

Request: brak.

Response: `BatchCertificate`.

Typowe bledy: `404`.

### GET `/bft/narwhal/dag`

Opis: zwraca widok DAG.

Request: brak.

Response: `NarwhalDagView`.

Typowe bledy: brak.

### GET `/bft/narwhal/tips`

Opis: zwraca aktualne tips DAG.

Request: brak.

Response: lista batch ids.

Typowe bledy: brak.

### DELETE `/bft/narwhal`

Opis: czysci stan Narwhal.

Request: brak.

Response: status czyszczenia.

Typowe bledy: brak.

## HotStuff

### POST `/bft/hotstuff/proposals`

Opis: tworzy proposal dla certyfikowanego batcha.

Request:

```json
{"batch_id":"batch-id","proposer_node_id":1}
```

Response: `HotStuffProposal`.

Typowe bledy: `404`, `409`, `422`.

### GET `/bft/hotstuff/proposals`

Opis: lista proposals.

Request: brak.

Response: lista `HotStuffProposal`.

Typowe bledy: brak.

### GET `/bft/hotstuff/proposals/{proposal_id}`

Opis: szczegoly proposal.

Request: brak.

Response: `HotStuffProposal`.

Typowe bledy: `404`.

### POST `/bft/hotstuff/proposals/{proposal_id}/vote`

Opis: zapisuje glos na proposal.

Request:

```json
{"voter_node_id":2,"accepted":true}
```

Response: vote i ewentualny QC.

Typowe bledy: `404`, `409`.

### POST `/bft/hotstuff/proposals/{proposal_id}/form-qc-demo`

Opis: lokalnie formuje quorum certificate.

Request: brak.

Response: `QuorumCertificate`.

Typowe bledy: `404`, `409`.

### GET `/bft/hotstuff/proposals/{proposal_id}/votes`

Opis: lista glosow dla proposal.

Request: brak.

Response: lista glosow.

Typowe bledy: `404`.

### GET `/bft/hotstuff/qc/{qc_id}`

Opis: szczegoly quorum certificate.

Request: brak.

Response: `QuorumCertificate`.

Typowe bledy: `404`.

### POST `/bft/hotstuff/qc/{qc_id}/commit`

Opis: tworzy commit certificate.

Request: brak.

Response: `CommitCertificate`.

Typowe bledy: `404`, `409`.

### GET `/bft/hotstuff/commits`

Opis: lista commitow.

Request: brak.

Response: lista `CommitCertificate`.

Typowe bledy: brak.

### GET `/bft/hotstuff/status`

Opis: status HotStuff view-state.

Request: brak.

Response: `HotStuffStatus`.

Typowe bledy: brak.

### POST `/bft/hotstuff/view-change-demo`

Opis: demonstracyjna zmiana widoku.

Request:

```json
{"reason":"demo_timeout"}
```

Response: `ViewState`.

Typowe bledy: brak.

### DELETE `/bft/hotstuff`

Opis: czysci stan HotStuff.

Request: brak.

Response: status czyszczenia.

Typowe bledy: brak.

## SWIM

### POST `/bft/swim/bootstrap`

Opis: inicjuje membership z konfiguracji wezla.

Request: brak.

Response: lista `SwimMember`.

Typowe bledy: brak.

### GET `/bft/swim/members`

Opis: lista czlonkow SWIM.

Request: brak.

Response: lista `SwimMember`.

Typowe bledy: brak.

### GET `/bft/swim/members/{node_id}`

Opis: szczegoly czlonka.

Request: brak.

Response: `SwimMember`.

Typowe bledy: `404`.

### GET `/bft/swim/status`

Opis: podsumowanie membership.

Request: brak.

Response: `SwimStatus`.

Typowe bledy: brak.

### POST `/bft/swim/ping/{target_node_id}`

Opis: wykonuje ping demonstracyjny.

Request: opcjonalny query `simulate_success=false`.

Response: `SwimProbeResult`.

Typowe bledy: `404`, `409`.

### POST `/bft/swim/ping-req`

Opis: wykonuje posredni ping przez inny wezel.

Request:

```json
{"intermediary_node_id":2,"target_node_id":3,"simulate_success":true}
```

Response: `SwimAck`.

Typowe bledy: `404`, `409`.

### POST `/bft/swim/probe-demo/{target_node_id}`

Opis: wykonuje direct + indirect probe.

Request:

```json
{"fail_direct":true,"fail_indirect":true}
```

Response: `SwimProbeResult`.

Typowe bledy: `404`.

### POST `/bft/swim/gossip`

Opis: aplikuje informacje gossip.

Request: `SwimGossipEnvelope`.

Response: `SwimStatus`.

Typowe bledy: `422`.

### PUT `/bft/swim/members/{node_id}/alive`

Opis: oznacza wezel jako `ALIVE`.

Request: brak.

Response: `SwimMember`.

Typowe bledy: `404`.

### PUT `/bft/swim/members/{node_id}/suspect`

Opis: oznacza wezel jako `SUSPECT`.

Request: brak.

Response: `SwimMember`.

Typowe bledy: `404`.

### PUT `/bft/swim/members/{node_id}/dead`

Opis: oznacza wezel jako `DEAD`.

Request: brak.

Response: `SwimMember`.

Typowe bledy: `404`.

### PUT `/bft/swim/members/{node_id}/recovering`

Opis: oznacza wezel jako `RECOVERING`.

Request: brak.

Response: `SwimMember`.

Typowe bledy: `404`.

### DELETE `/bft/swim`

Opis: czysci stan SWIM.

Request: brak.

Response: status czyszczenia.

Typowe bledy: brak.

## Fault injection

### POST `/bft/faults/rules`

Opis: tworzy regule fault injection.

Request:

```json
{"fault_type":"DROP","protocol":"HOTSTUFF","message_kind":"VOTE","probability":1.0}
```

Response: `FaultRule`.

Typowe bledy: `422`.

### GET `/bft/faults/rules`

Opis: lista regul.

Request: brak.

Response: lista `FaultRule`.

Typowe bledy: brak.

### GET `/bft/faults/rules/{rule_id}`

Opis: szczegoly reguly.

Request: brak.

Response: `FaultRule`.

Typowe bledy: `404`.

### PUT `/bft/faults/rules/{rule_id}/enable`

Opis: wlacza regule.

Request: brak.

Response: `FaultRule`.

Typowe bledy: `404`.

### PUT `/bft/faults/rules/{rule_id}/disable`

Opis: wylacza regule.

Request: brak.

Response: `FaultRule`.

Typowe bledy: `404`.

### DELETE `/bft/faults/rules/{rule_id}`

Opis: usuwa regule.

Request: brak.

Response: status usuniecia.

Typowe bledy: `404`.

### POST `/bft/faults/partitions`

Opis: tworzy partycje sieci.

Request:

```json
{"groups":[[1,2,3],[4,5,6]]}
```

Response: `NetworkPartition`.

Typowe bledy: `422`.

### GET `/bft/faults/partitions`

Opis: lista partycji.

Request: brak.

Response: lista `NetworkPartition`.

Typowe bledy: brak.

### PUT `/bft/faults/partitions/{partition_id}/enable`

Opis: wlacza partycje.

Request: brak.

Response: `NetworkPartition`.

Typowe bledy: `404`.

### PUT `/bft/faults/partitions/{partition_id}/disable`

Opis: wylacza partycje.

Request: brak.

Response: `NetworkPartition`.

Typowe bledy: `404`.

### DELETE `/bft/faults/partitions/{partition_id}`

Opis: usuwa partycje.

Request: brak.

Response: status usuniecia.

Typowe bledy: `404`.

### POST `/bft/faults/evaluate`

Opis: ocenia, czy komunikat ma byc przepuszczony, opozniony lub zablokowany.

Request:

```json
{"protocol":"HOTSTUFF","message_kind":"VOTE","source_node_id":1,"target_node_id":4,"message_id":"vote-1"}
```

Response: `FaultDecision`.

Typowe bledy: `422`.

### GET `/bft/faults/status`

Opis: status fault injection.

Request: brak.

Response: `FaultInjectionStatus`.

Typowe bledy: brak.

### GET `/bft/faults/injected`

Opis: lista wstrzyknietych awarii.

Request: brak.

Response: lista `InjectedFault`.

Typowe bledy: brak.

### GET `/bft/faults/equivocation/conflicts`

Opis: lista wykrytych konfliktow equivocation.

Request: brak.

Response: lista konfliktow.

Typowe bledy: brak.

### DELETE `/bft/faults`

Opis: czysci fault injection.

Request: brak.

Response: status czyszczenia.

Typowe bledy: brak.

## Checkpointing

### POST `/bft/checkpointing/snapshots`

Opis: tworzy snapshot stanu.

Request:

```json
{"node_id":1}
```

Response: `StateSnapshot`.

Typowe bledy: `409`.

### GET `/bft/checkpointing/snapshots`

Opis: lista snapshotow.

Request: brak.

Response: lista `StateSnapshot`.

Typowe bledy: brak.

### GET `/bft/checkpointing/snapshots/{snapshot_id}`

Opis: szczegoly snapshotu.

Request: brak.

Response: `StateSnapshot`.

Typowe bledy: `404`.

### POST `/bft/checkpointing/snapshots/{snapshot_id}/certify`

Opis: certyfikuje snapshot demonstracyjnym quorum.

Request:

```json
{"total_nodes":6}
```

Response: `CheckpointCertificate`.

Typowe bledy: `404`, `409`.

### GET `/bft/checkpointing/certificates/{checkpoint_id}`

Opis: szczegoly certyfikatu checkpointu.

Request: brak.

Response: `CheckpointCertificate`.

Typowe bledy: `404`.

### GET `/bft/checkpointing/status`

Opis: status checkpointingu.

Request: brak.

Response: `CheckpointStatus`.

Typowe bledy: brak.

### DELETE `/bft/checkpointing`

Opis: czysci checkpointing.

Request: brak.

Response: status czyszczenia.

Typowe bledy: brak.

## Recovery

### POST `/bft/recovery/state-transfer`

Opis: tworzy request state transfer dla wezla.

Request:

```json
{"node_id":3,"checkpoint_id":"checkpoint-id","reason":"demo_state_corruption"}
```

Response: `StateTransferRequest`.

Typowe bledy: `404`, `409`.

### POST `/bft/recovery/state-transfer/{node_id}/response`

Opis: buduje odpowiedz state transfer dla wezla.

Request: brak.

Response: `StateTransferResponse`.

Typowe bledy: `404`, `409`.

### POST `/bft/recovery/nodes/{node_id}/apply`

Opis: aplikuje przygotowany state transfer.

Request: brak.

Response: `RecoveryResult`.

Typowe bledy: `404`, `409`.

### POST `/bft/recovery/nodes/{node_id}/recover-demo`

Opis: wykonuje pelne recovery demo dla wezla.

Request:

```json
{"checkpoint_id":"checkpoint-id"}
```

Response: `RecoveryResult`.

Typowe bledy: `404`, `409`.

### GET `/bft/recovery/status`

Opis: status recovery.

Request: brak.

Response: `RecoveryStatus`.

Typowe bledy: brak.

### DELETE `/bft/recovery`

Opis: czysci recovery.

Request: brak.

Response: status czyszczenia.

Typowe bledy: brak.

## Crypto

### POST `/bft/crypto/demo-keys`

Opis: generuje klucze demo dla wezlow.

Request: query `total_nodes=6`.

Response: publiczne informacje o kluczach.

Typowe bledy: `422`.

### GET `/bft/crypto/public-keys`

Opis: lista kluczy publicznych demo.

Request: brak.

Response: lista kluczy publicznych.

Typowe bledy: brak.

### POST `/bft/crypto/sign`

Opis: podpisuje komunikat BFT.

Request:

```json
{"protocol":"HOTSTUFF","message_kind":"VOTE","source_node_id":1,"body":{"proposal_id":"p1"}}
```

Response: `BftSignedMessage`.

Typowe bledy: `404`, `422`.

### POST `/bft/crypto/verify`

Opis: weryfikuje podpis i replay dla komunikatu.

Request: `BftSignedMessage`.

Response: `BftVerificationResult`.

Typowe bledy: `422`.

### POST `/bft/crypto/verify/{protocol}`

Opis: weryfikuje podpis i dodatkowo oczekiwany protokol.

Request: `BftSignedMessage`.

Response: `BftVerificationResult`.

Typowe bledy: `422`.

### DELETE `/bft/crypto`

Opis: czysci klucze i replay guard.

Request: brak.

Response: status czyszczenia.

Typowe bledy: brak.

## Observability

### GET `/bft/observability/health`

Opis: health check modulow BFT.

Request: brak.

Response: `BftSystemHealth`.

Typowe bledy: brak.

### GET `/bft/observability/metrics`

Opis: metryki w formacie Prometheus text.

Request: brak.

Response: `text/plain`.

Typowe bledy: brak.

### GET `/bft/observability/metrics/snapshot`

Opis: JSON snapshot metryk.

Request: brak.

Response: slownik licznikow i gauge.

Typowe bledy: brak.

## Demo

### POST `/bft/demo/run`

Opis: uruchamia finalny scenariusz demonstracyjny.

Request: brak.

Response: `BftDemoReport` ze statusem, krokami, `operation_id`, `checkpoint_id`, `recovered_node_id` i `metrics_snapshot`.

Typowe bledy: raport moze miec `status: error`, jesli ktorys krok rzuci wyjatek.

### GET `/bft/demo/last-report`

Opis: zwraca ostatni raport demo.

Request: brak.

Response: `BftDemoReport`.

Typowe bledy: `404`, jesli demo nie bylo uruchomione.

### DELETE `/bft/demo/last-report`

Opis: usuwa ostatni raport demo.

Request: brak.

Response: status usuniecia.

Typowe bledy: brak.
