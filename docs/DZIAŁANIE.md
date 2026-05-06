1. Klient wysyła operację
   POST /bft/client/submit
2. Operacja trafia do OPERATION_STORE
   status = RECEIVED
3. Narwhal tworzy batch
   POST /bft/narwhal/batches
4. Narwhal zapisuje batch jako vertex DAG
   status operacji: RECEIVED → BATCHED
5. Node’y ACKują batch
   POST /bft/narwhal/batches/{batch_id}/ack
6. Po quorum ACK powstaje BatchCertificate
   status operacji: BATCHED → AVAILABLE
7. HotStuff tworzy proposal dla batcha
   POST /bft/hotstuff/proposals
8. Operacja przechodzi:
   AVAILABLE → PROPOSED
9. Node’y głosują
   POST /bft/hotstuff/proposals/{proposal_id}/vote
10. Po quorum głosów powstaje QC
    PROPOSED → VOTED → QC_FORMED
11. Commit przez QC
    POST /bft/hotstuff/qc/{qc_id}/commit
12. Operacja przechodzi:
    QC_FORMED → COMMITTED
13. SWIM równolegle pilnuje, które node’y są ALIVE/SUSPECT/DEAD/RECOVERING
14. EventLog, metrics i dashboard pokazują przebieg
