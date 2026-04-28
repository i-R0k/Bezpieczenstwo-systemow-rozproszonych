# SWIM

Ten dokument opisuje lokalna warstwe SWIM membership dodana w piatym etapie refaktoru. Implementacja jest demonstracyjna: nie uruchamia background taskow i nie wykonuje prawdziwego HTTP pingowania peerow.

## Cel modulu

SWIM dostarcza BFT informacje o czlonkach klastra i ich stanie operacyjnym:

- bootstrap membership z konfiguracji wezla;
- statusy `ALIVE`, `SUSPECT`, `DEAD`, `RECOVERING`;
- demonstracyjny direct ping i ACK;
- demonstracyjny indirect `ping-req`;
- gossip updates z incarnation;
- minimalna integracja z HotStuff eligibility.

## Modele

- `SwimMember` - wezel, adres, status, incarnation, last_seen i suspicion_count.
- `SwimPing` - direct ping.
- `SwimAck` - odpowiedz na ping albo ping-req.
- `SwimPingReq` - prosba o posrednie sprawdzenie targetu.
- `SwimGossipUpdate` - pojedynczy update membership.
- `SwimGossipEnvelope` - paczka gossip updates.
- `SwimStatus` - diagnostyczny widok membership.
- `SwimProbeResult` - wynik direct ping i ewentualnych indirect probes.

## Endpointy

- `POST /bft/swim/bootstrap` - buduje membership z `CONFIG.node_id` i `CONFIG.peers`.
- `GET /bft/swim/members` - lista members.
- `GET /bft/swim/members/{node_id}` - pojedynczy member.
- `GET /bft/swim/status` - counts i lista members.
- `POST /bft/swim/ping/{target_node_id}` - demo direct ping.
- `POST /bft/swim/ping-req` - demo indirect ping.
- `POST /bft/swim/probe-demo/{target_node_id}` - direct ping, a po porazce ping-req przez maksymalnie 2 wezly ALIVE.
- `POST /bft/swim/gossip` - stosuje gossip updates.
- `PUT /bft/swim/members/{node_id}/alive` - mark alive.
- `PUT /bft/swim/members/{node_id}/suspect` - mark suspect.
- `PUT /bft/swim/members/{node_id}/dead` - mark dead.
- `PUT /bft/swim/members/{node_id}/recovering` - mark recovering.
- `DELETE /bft/swim` - czysci membership.

## Statusy i przejscia

```text
ALIVE -> SUSPECT -> DEAD
DEAD -> ALIVE      # zwieksza incarnation
ALIVE -> RECOVERING -> ALIVE
```

`mark_suspect` zwieksza `suspicion_count`. W service dwa nieudane direct pingi moga oznaczyc wezel jako `DEAD`. `mark_alive` zeruje `suspicion_count`; jesli wezel byl `DEAD`, zwieksza incarnation.

## Ping, ping-req i gossip

`ping` tworzy `SwimPing`. Przy sukcesie oznacza target jako `ALIVE` i zwraca `SwimAck`. Przy porazce oznacza target jako `SUSPECT`, a po progu podejrzen jako `DEAD`.

`ping-req` w tej wersji nie wykonuje sieci. Intermediary zwraca symulowany ACK targetu.

`gossip` stosuje update tylko wtedy, gdy ma nowsza incarnation albo przy tej samej incarnation ma silniejszy status:

```text
ALIVE < RECOVERING < SUSPECT < DEAD
```

Pusta lista gossip updates jest odrzucana przez router HTTP 400, zeby uniknac mylacych no-opow w demonstracji.

## Integracja z HotStuff

HotStuff sprawdza membership przed proposal i vote. Wezel `DEAD`, `SUSPECT` albo `RECOVERING` nie jest eligible do konsensusu. Brak wpisu SWIM oznacza tryb kompatybilnosci i nie blokuje HotStuff.

SWIM nie zmienia jeszcze leader election. Lider HotStuff pozostaje liczony przez pacemaker demo.

## Ograniczenia aktualnej implementacji

- Stan jest in-memory.
- Brak background taskow.
- Brak prawdziwych HTTP pingow.
- Brak losowego wyboru probe targetow.
- Brak okresowego gossip fanout.
- Brak integracji z metrykami.
- Brak state transfer dla `RECOVERING`.

## Plan rozbudowy

Kolejny etap powinien dodac:

- okresowy background probing;
- prawdziwy HTTP ping/ping-req do peerow;
- losowanie targetow i intermediary;
- gossip fanout;
- metryki membership;
- korelacje fault injection z failure detection;
- feed statusow SWIM do dashboardow i scenariuszy demo.
