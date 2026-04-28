# Checkpointing i Recovery

## Cel

Warstwa checkpointing/recovery utrwala deterministyczny obraz stanu po commitach HotStuff i pokazuje demonstracyjny state transfer dla wezla, ktory utracil stan albo wraca po awarii.

## Przeplyw

```text
COMMITTED operations
   -> deterministic state snapshot
   -> checkpoint hash
   -> checkpoint certificate
   -> node crash / stale state
   -> state transfer request
   -> apply checkpoint
   -> replay committed operations after checkpoint
   -> RECOVERED / ALIVE
```

## Modele

- `StateSnapshot` - deterministyczny snapshot operacji `COMMITTED` i `EXECUTED`.
- `CheckpointCertificate` - certyfikat checkpointu tworzony po quorum signerow `2f + 1`.
- `StateTransferRequest` - prosba wezla o stan z checkpointu.
- `StateTransferResponse` - snapshot plus lista committed operations po checkpointcie.
- `RecoveryResult` - wynik zastosowania checkpointu i replayu.

## Endpointy

- `POST /bft/checkpointing/snapshots`
- `GET /bft/checkpointing/snapshots`
- `GET /bft/checkpointing/snapshots/{snapshot_id}`
- `POST /bft/checkpointing/snapshots/{snapshot_id}/certify`
- `GET /bft/checkpointing/certificates/{checkpoint_id}`
- `GET /bft/checkpointing/status`
- `DELETE /bft/checkpointing`
- `POST /bft/recovery/state-transfer`
- `POST /bft/recovery/state-transfer/{node_id}/response`
- `POST /bft/recovery/nodes/{node_id}/apply`
- `POST /bft/recovery/nodes/{node_id}/recover-demo`
- `GET /bft/recovery/status`
- `DELETE /bft/recovery`

## Ograniczenia

Snapshot jest pamieciowy i demonstracyjny. Nie wykonuje jeszcze rzeczywistej serializacji stanu domeny VetClinic, transferu HTTP miedzy node'ami ani walidacji podpisow checkpoint certificate. To przygotowuje kontrakt pod pelny state transfer i kryptografie w kolejnych etapach.
