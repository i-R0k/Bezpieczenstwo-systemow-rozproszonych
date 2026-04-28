# Bezpieczenstwo komunikatow BFT

## Cel warstwy crypto

`vetclinic_api.bft.crypto` dodaje lokalny kontrakt bezpieczenstwa komunikatow BFT: klucze per-node, Ed25519, canonical JSON, envelope, `message_id`, nonce, weryfikacje podpisu i replay protection. Nie usuwa starszego `vetclinic_api/crypto/ed25519.py`.

## NodeKeyPair

`NodeKeyPair` przechowuje `node_id`, publiczny klucz base64 oraz opcjonalny prywatny klucz base64. Publiczny widok registry nigdy nie ujawnia `private_key_b64`.

## Canonical JSON

`canonical_json_bytes` serializuje dane deterministycznie:

- `sort_keys=True`;
- `separators=(",", ":")`;
- datetime jako ISO 8601;
- enumy przez `value`;
- modele Pydantic przez `model_dump(mode="json")`.

## Message Envelope

`BftMessagePayload` opisuje protokol, rodzaj komunikatu, source/target node, korelacje i body. `BftSignedMessage` zawiera:

- `message_id = sha256(canonical(payload + nonce))`;
- `nonce`;
- payload;
- podpis Ed25519;
- publiczny klucz source node;
- timestamp podpisu.

Podpis obejmuje dokladnie canonical material z payloadem i nonce. `message_id` nie obejmuje podpisu.

## ReplayGuard

CryptoService uzywa tego samego `REPLAY_GUARD`, ktory istnieje w fault injection. Pierwsza weryfikacja komunikatu oznacza `message_id` jako widziany. Druga weryfikacja tego samego message zwraca `valid=false`, `replay=true`, `reason="replay_detected"`.

## Public Key Registry

`NODE_KEY_REGISTRY` przechowuje klucze w pamieci. Endpoint `/bft/crypto/demo-keys` generuje demo keys dla node'ow 1..N. To nie jest trwale PKI.

## Integracje

- Narwhal podpisuje `BATCH` i `BATCH_ACK`, a eventy zawieraja `signed_message_id`.
- HotStuff podpisuje `PROPOSAL` i `VOTE`.
- SWIM podpisuje `SWIM_PING`, `SWIM_ACK` i `SWIM_GOSSIP`.
- Checkpointing podpisuje checkpoint vote jako `CHECKPOINT`.
- Recovery podpisuje `STATE_TRANSFER` request/response.

## Endpointy

- `POST /bft/crypto/demo-keys`
- `GET /bft/crypto/public-keys`
- `POST /bft/crypto/sign`
- `POST /bft/crypto/verify`
- `POST /bft/crypto/verify/{protocol}`
- `DELETE /bft/crypto`

## Ograniczenia

- Brak realnego mTLS w tym etapie.
- Demo keys sa in-memory.
- Brak trwalego PKI i certyfikatow X.509.
- QC i checkpoint certificate nie przechowuja jeszcze pelnego zestawu podpisow jako czesci modeli konsensusu; podpisane envelope sa widoczne w `EventLog`.
