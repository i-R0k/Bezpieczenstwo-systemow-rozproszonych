# HotStuff

Ten dokument opisuje lokalna warstwe HotStuff dodana w czwartym etapie refaktoru. Implementacja jest modelem demonstracyjnym proposal, vote, quorum certificate, commit oraz podstawowego pacemakera. Nie jest jeszcze pelnym protokolem sieciowym.

## Cel modulu

HotStuff przyjmuje certyfikowane batche z Narwhal i ustala ich kolejny status w procesie BFT:

- tworzy proposal na podstawie `BatchCertificate`;
- zbiera glosy;
- tworzy `QuorumCertificate` po quorum;
- commituje blok i operacje z batcha;
- utrzymuje prosty `ViewState`;
- symuluje timeout certificate oraz view-change.

## Modele

- `HotStuffBlock` - blok logiczny wskazujacy `batch_id`, widok, wysokosc, parent i `payload_hash`.
- `HotStuffProposal` - proposal bloku wraz z referencja do certyfikatu batcha.
- `HotStuffVote` - glos wezla dla proposal.
- `QuorumCertificate` - quorum zaakceptowanych glosow dla proposal.
- `CommitCertificate` - commit bloku i operacji.
- `ViewState` - aktualny view, lider, high QC, locked QC, ostatni commit.
- `TimeoutVote` - glos timeout dla view.
- `TimeoutCertificate` - quorum timeout votes.
- `HotStuffStatus` - diagnostyczny stan HotStuff.

## Endpointy

- `POST /bft/hotstuff/proposals` - tworzy proposal dla certyfikowanego batcha.
- `GET /bft/hotstuff/proposals` - lista proposal.
- `GET /bft/hotstuff/proposals/{proposal_id}` - szczegoly proposal.
- `POST /bft/hotstuff/proposals/{proposal_id}/vote` - dodaje glos.
- `POST /bft/hotstuff/proposals/{proposal_id}/form-qc-demo` - lokalnie dodaje glosy do quorum.
- `GET /bft/hotstuff/proposals/{proposal_id}/votes` - lista glosow.
- `GET /bft/hotstuff/qc/{qc_id}` - pobiera QC.
- `POST /bft/hotstuff/qc/{qc_id}/commit` - commit na podstawie QC.
- `GET /bft/hotstuff/commits` - lista commitow.
- `GET /bft/hotstuff/status` - status HotStuff.
- `POST /bft/hotstuff/view-change-demo` - demo timeout quorum i advance view.
- `DELETE /bft/hotstuff` - czysci stan HotStuff.

## Przeplyw

```text
NarwhalBatch + BatchCertificate(available=true)
  -> HotStuffProposal
  -> HotStuffVote
  -> QuorumCertificate
  -> CommitCertificate
  -> OperationStatus.COMMITTED
```

`/bft/operations/{operation_id}/run-demo` korzysta teraz z Narwhal dla `BATCHED` i `AVAILABLE`, a nastepnie z HotStuff dla `PROPOSED`, `VOTED`, `QC_FORMED` i `COMMITTED`. `EXECUTED` pozostaje osobnym logicznym etapem demo.

## Quorum

Quorum jest liczone wspolna funkcja `common/quorum.py`:

```text
f = floor((n - 1) / 3)
quorum = 2f + 1
```

Dla `n=6` quorum wynosi `3`, a tolerancja bledow `f=1`. Nie jest to zwykla wiekszosc.

## View-change demo

Pacemaker jest uproszczony. Lider widoku:

```text
leader_node_id = (view % total_nodes) + 1
```

`POST /bft/hotstuff/view-change-demo` tworzy lokalne timeout votes od kolejnych node ids az do quorum, tworzy `TimeoutCertificate`, a nastepnie zwieksza view i wyznacza nowego lidera.

## Ograniczenia aktualnej implementacji

- Stan jest in-memory.
- Glosy nie maja podpisow.
- Brak prawdziwego broadcastu proposal/vote/commit.
- Brak walidacji kryptograficznej lidera.
- Brak pelnego three-chain commit rule.
- Brak integracji z wykonaniem domenowym VetClinic i legacy blockchainem.
- Pacemaker nie ma realnych timeoutow ani synchronizacji zegara.

## Plan rozbudowy

Kolejny etap HotStuff powinien dodac:

- podpisy proposal i vote;
- sieciowy broadcast proposal do peerow;
- endpoint odbioru glosow z walidacja podpisow;
- przechowywanie high QC i locked QC zgodnie z reguly bezpieczenstwa;
- realny pacemaker z timeoutami;
- integracje z metrykami;
- jasne przekazanie committed batch do state machine.

Nastepny punkt planu dotyczy SWIM membership. SWIM powinien dostarczac HotStuffowi informacje o aktywnych, podejrzanych i martwych wezlach bez zastapienia quorum BFT.
