# Fault Injection BFT

## Cel modulu

`vetclinic_api.bft.fault_injection` jest protokolowa warstwa symulowania awarii dla BFT. Nie usuwa starszego mechanizmu chaos/admin. Dziala lokalnie, w pamieci i bez prawdziwej sieci, zeby testy Narwhal, HotStuff i SWIM mogly sprawdzac zachowanie przy kontrolowanych bledach.

## Modele

- `FaultRule` - aktywna regula awarii filtrowana po protokole, source/target node i rodzaju komunikatu.
- `InjectedFault` - zapis konkretnego zastosowania reguly.
- `FaultDecision` - wynik ewaluacji: drop, delay, duplicate, replay, equivocation, partition albo leader failure.
- `NetworkPartition` - podzial node'ow na grupy; komunikacja miedzy grupami jest blokowana.
- `FaultEvaluationContext` - kontekst komunikatu ocenianego przez fault injection.

## ReplayGuard

`ReplayGuard` pamieta `message_id`. Pierwsze wystapienie nie jest replay, drugie z tym samym `message_id` jest replay. To nie jest jeszcze pelna ochrona kryptograficzna; podpisy i nonce beda czescia etapu crypto/mTLS.

## EquivocationDetector

`EquivocationDetector` zapisuje proposal dla pary `(view, proposer_node_id)`. Konflikt wystepuje, gdy ten sam proposer w tym samym view pokazuje rozne `block_id`.

## Endpointy

- `POST /bft/faults/rules`
- `GET /bft/faults/rules`
- `GET /bft/faults/rules/{rule_id}`
- `PUT /bft/faults/rules/{rule_id}/enable`
- `PUT /bft/faults/rules/{rule_id}/disable`
- `DELETE /bft/faults/rules/{rule_id}`
- `POST /bft/faults/partitions`
- `GET /bft/faults/partitions`
- `PUT /bft/faults/partitions/{partition_id}/enable`
- `PUT /bft/faults/partitions/{partition_id}/disable`
- `DELETE /bft/faults/partitions/{partition_id}`
- `POST /bft/faults/evaluate`
- `GET /bft/faults/status`
- `GET /bft/faults/injected`
- `GET /bft/faults/equivocation/conflicts`
- `DELETE /bft/faults`

## Integracja z Narwhal

Narwhal ocenia `BATCH` i `BATCH_ACK`.

- `DROP` albo aktywna partycja blokuje utworzenie batcha lub ACK.
- `DELAY` zapisuje symulowany delay w eventach, bez usypiania testu.
- `DUPLICATE` nie tworzy realnego duplikatu batcha; ACK pozostaje idempotentny.

## Integracja z HotStuff

HotStuff ocenia `PROPOSAL`, `VOTE` i `COMMIT`.

- `DROP`, `NETWORK_PARTITION` i `LEADER_FAILURE` blokuja proposal/vote/commit przez blad domenowy mapowany w routerze na HTTP 409.
- `REPLAY` uzywa `ReplayGuard`, zeby drugi taki sam vote/commit nie zmienial stanu.
- `EQUIVOCATION` zapisuje konflikt w `EquivocationDetector`, ale nie psuje normalnej sciezki demonstracyjnej.

## Integracja z SWIM

SWIM ocenia `SWIM_PING`, `SWIM_ACK` dla ping-req oraz `SWIM_GOSSIP`.

- `DROP` ping traktowany jest jak missed ACK, wiec node przechodzi do `SUSPECT`, a po kolejnym braku ACK do `DEAD`.
- Partycja miedzy source i target dziala jak drop.
- `DELAY` zapisuje event `swim_ping_delay_simulated`.
- `DROP` gossip blokuje zastosowanie update.

## Ograniczenia

- Nie ma prawdziwego opozniania (`sleep`) w testach.
- Nie ma prawdziwego broadcastu HTTP do peerow.
- Replay jest wykrywany po `message_id`, bez podpisow.
- State corruption jest placeholderem do etapu checkpointing/state transfer.
- mTLS, podpisy i pelna ochrona replay beda czescia kolejnych etapow.
