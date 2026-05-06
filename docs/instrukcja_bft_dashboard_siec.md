# Instrukcja obsługi BFT Dashboard oraz zakładki Sieć

> Uwaga: w projekcie poprawną nazwą jest **BFT Dashboard**, nie „DFT Dashboard”. System dotyczy odporności bizantyjskiej i protokołów Narwhal, HotStuff oraz SWIM.

## 1. Cel paneli

System służy do demonstracji odpornego na błędy systemu rozproszonego. Najważniejsze funkcje przewidziane w harmonogramie to wizualizacja topologii i stanu klastra, fault injection, monitoring komunikacji między węzłami, 2FA, checkpointing oraz odtwarzanie stanu.

W projekcie są dwa powiązane, ale różne widoki:

**BFT Dashboard** pokazuje logikę protokołów BFT: Narwhal, HotStuff, SWIM, fault injection, checkpointing, recovery, gRPC, TOTP i status transportu.

**Zakładka Sieć** pokazuje bardziej operacyjny widok klastra: adresy node’ów, wysokości łańcucha, hash ostatniego bloku, wynik weryfikacji, błędy RPC oraz prostą symulację ruchu i awarii.

Nie należy tych widoków traktować jako tego samego panelu. BFT Dashboard odpowiada za demonstrację protokołów, a Sieć za diagnostykę działania klastra i legacy chain/RPC.

---

## 2. Uruchomienie środowiska

### 2.1. Uruchomienie klastra Docker

Z katalogu głównego repozytorium:

```bash
docker compose down --remove-orphans
docker compose build --no-cache
docker compose up -d node1 node2 node3 node4 node5 node6
```

Porty hosta:

| Węzeł | URL z hosta |
|---|---|
| node1 | `http://127.0.0.1:8001` |
| node2 | `http://127.0.0.1:8002` |
| node3 | `http://127.0.0.1:8003` |
| node4 | `http://127.0.0.1:8004` |
| node5 | `http://127.0.0.1:8005` |
| node6 | `http://127.0.0.1:8006` |

Adres `http://127.0.0.1:8000` oznacza tryb standalone, a nie sześciowęzłowy klaster. Jeżeli dashboard pokazuje `Total nodes = 1`, prawie zawsze oznacza to połączenie z API standalone zamiast z `node1`.

### 2.2. Uruchomienie BFT Dashboard

```bash
python VetClinic/GUI/run_bft_dashboard.py --base-url http://127.0.0.1:8001
```

Alternatywnie:

```bash
set BFT_DASHBOARD_BASE_URL=http://127.0.0.1:8001
python VetClinic/GUI/run_bft_dashboard.py
```

W trybie Docker poprawnym adresem bazowym jest:

```text
http://127.0.0.1:8001
```

---

## 3. Górny pasek BFT Dashboard

BFT Dashboard ma górny pasek sterowania i zakładki:

- `Overview`,
- `Protocols`,
- `Live logs`,
- `Demo actions`,
- `Fault injection`,
- `Security / 2FA / transport`.

### Base URL

Pole wskazuje backend, z którym łączy się GUI.

Poprawne wartości:

```text
http://127.0.0.1:8001
```

dla klastra Docker albo:

```text
http://127.0.0.1:8000
```

dla pojedynczego API standalone.

Do demonstracji sześciowęzłowego klastra należy używać `8001`.

### Environment

Lista presetów środowiska.

| Preset | Znaczenie |
|---|---|
| Standalone API | pojedynczy backend bez PEERS |
| Docker node1 | wejście do sześciowęzłowego klastra przez node1 |

Jeżeli celem jest prezentacja BFT, wybierz **Docker node1**.

### Admin token

Token administracyjny używany, gdy backend działa w trybie strict. Bez tokenu część operacji administracyjnych, np. fault injection albo reset, może zostać odrzucona.

### Connect/Test

Sprawdza połączenie z backendem.

Po poprawnym połączeniu status na dole powinien pokazać adres API i czas ostatniego odświeżenia.

### Auto-refresh

Włącza automatyczne odświeżanie dashboardu.

Przy demonstracji najlepiej zostawić włączone.

### Interwał odświeżania

Dostępne wartości: `1s`, `2s`, `5s`.

Do prezentacji działania w czasie rzeczywistym użyj `1s` albo `2s`. Przy dużym ruchu lepiej użyć `5s`, żeby GUI nie generowało zbyt wielu zapytań.

### Refresh now

Ręcznie odświeża wszystkie sekcje.

---

## 4. Zakładka Overview

Zakładka **Overview** daje szybki stan całego systemu.

### Total nodes

Liczba węzłów widziana przez backend.

Dla klastra Docker oczekiwana wartość:

```text
6
```

Jeżeli jest:

```text
1
```

to najczęściej dashboard jest połączony z `http://127.0.0.1:8000`, czyli standalone API.

### Quorum

Liczba głosów wymagana do zatwierdzenia operacji.

Dla klastra sześciowęzłowego quorum powinno odpowiadać konfiguracji BFT wyliczonej przez backend. To pole służy do pokazania, że system nie zatwierdza operacji dowolnie, tylko wymaga minimalnej liczby poprawnych replik.

### Current leader

Aktualny lider w widoku HotStuff.

Lider tworzy propozycje, które następnie są głosowane przez repliki.

### Current view

Numer aktualnego widoku HotStuff.

Zmiana view oznacza przejście do kolejnej rundy konsensusu albo reakcję na problem z liderem.

### Operation count

Liczba operacji klienta zarejestrowanych przez warstwę BFT.

Rośnie po wykonaniu scenariuszy demo lub po submitowaniu operacji.

### Batch count

Liczba batchy utworzonych przez Narwhal.

Narwhal odpowiada za grupowanie operacji i dostępność danych przed konsensusem.

### Proposal count

Liczba propozycji HotStuff.

Proposal oznacza próbę uporządkowania batcha lub operacji przez lidera.

### QC count

Liczba quorum certificates.

QC potwierdza, że uzyskano wymagane kworum głosów.

### Commit count

Liczba commitów.

Commit oznacza zatwierdzenie operacji w logice konsensusu.

### Checkpoint count

Liczba certyfikatów checkpointu.

Checkpoint jest punktem odtworzeniowym stanu systemu.

### Active faults

Liczba aktywnych reguł fault injection.

Jeżeli wartość jest większa niż zero, wyniki konsensusu mogą być celowo zaburzane przez symulowane błędy.

### Cluster nodes

Sekcja pokazuje statusy `node1`–`node6`.

Typowe statusy:

| Status | Znaczenie |
|---|---|
| ALIVE | węzeł działa poprawnie |
| SUSPECT | SWIM podejrzewa awarię lub problem z komunikacją |
| DEAD | węzeł uznany za niedostępny |
| RECOVERING | węzeł jest w trakcie odzyskiwania |
| UNKNOWN | dashboard nie dostał jeszcze informacji o statusie |

---

## 5. Zakładka Protocols

Zakładka **Protocols** pokazuje stan poszczególnych protokołów.

### Narwhal

Pola:

| Pole | Znaczenie |
|---|---|
| Narwhal batches | liczba batchy operacji |
| DAG batches | liczba batchy w DAG |
| DAG tips | końcówki DAG, czyli aktualne „liście” struktury danych |

Narwhal służy do batchowania operacji i zapewnienia data availability. W scenariuszu prezentacyjnym należy pokazać, że po wysłaniu operacji rośnie liczba batchy.

### HotStuff

Pola:

| Pole | Znaczenie |
|---|---|
| HotStuff view | numer widoku/rundy |
| HotStuff leader | aktualny lider |
| Proposals | liczba propozycji |
| QCs | liczba quorum certificates |
| Commits | liczba commitów |

HotStuff odpowiada za uporządkowanie operacji i decyzję konsensusu. W prezentacji należy pokazać zależność:

```text
operacja → batch Narwhal → proposal HotStuff → głosy → QC → commit
```

### SWIM

Pola:

| Pole | Znaczenie |
|---|---|
| SWIM alive | liczba aktywnych węzłów |
| SWIM suspect | liczba podejrzanych węzłów |
| SWIM dead | liczba martwych węzłów |
| SWIM recovering | liczba odzyskiwanych węzłów |

SWIM odpowiada za membership i failure detection. To jest główny widok do demonstracji wykrywania awarii.

### Checkpointing

Pola:

| Pole | Znaczenie |
|---|---|
| Snapshots | liczba snapshotów stanu |
| Certificates | liczba certyfikatów checkpointu |

Checkpointing pozwala odtworzyć stan bez wykonywania całej historii od początku.

### Recovery

Pola:

| Pole | Znaczenie |
|---|---|
| Transfers | liczba transferów stanu |
| Recovered nodes | liczba węzłów odtworzonych po awarii |

Recovery pokazuje mechanizm synchronizacji węzła po problemie.

---

## 6. Zakładka Live logs

Zakładka **Live logs** służy do śledzenia zdarzeń systemowych.

### Protocol filter

Filtruje logi według protokołu:

| Filtr | Znaczenie |
|---|---|
| ALL | wszystkie zdarzenia |
| NARWHAL | batchowanie i DAG |
| HOTSTUFF | proposal, vote, QC, commit |
| SWIM | membership i failure detection |
| FAULT_INJECTION | aktywacja i skutki błędów |
| CHECKPOINTING | snapshoty i checkpoint certificates |
| RECOVERY | state transfer i odtwarzanie |
| CRYPTO | podpisy, weryfikacja, replay protection |

### Communication log

Pokazuje komunikaty między komponentami/węzłami.

Przydatne kolumny:

| Kolumna | Znaczenie |
|---|---|
| timestamp | czas zdarzenia |
| protocol | protokół |
| kind | typ wiadomości |
| source | węzeł źródłowy |
| target | węzeł docelowy |
| operation | identyfikator operacji |
| message | opis zdarzenia |

### Recent events

Pokazuje zdarzenia logiczne w systemie, np. przyjęcie operacji, utworzenie batcha, proposal, głosowanie, commit, checkpoint albo błąd.

---

## 7. Zakładka Demo actions

Zakładka **Demo actions** służy do szybkiego uruchamiania gotowych scenariuszy.

### Run full BFT demo

Uruchamia pełny scenariusz demonstracyjny.

Powinien pokazać:

```text
operacja klienta
Narwhal batch
HotStuff proposal
vote
QC
commit
checkpoint
recovery
metryki
raport końcowy
```

To najlepszy przycisk na początek prezentacji, bo w jednym przebiegu pokazuje większość elementów z harmonogramu: konsensus, membership, checkpointing, recovery, observability i logi.

### Run gRPC ping demo

Uruchamia demonstrację komunikacji gRPC.

Służy do pokazania, że projekt posiada kontrakt komunikacyjny i runtime demo dla komunikacji międzywęzłowej.

### Refresh all

Odświeża wszystkie dane w dashboardzie.

### Open last report JSON

Otwiera ostatni raport demo w formacie JSON.

W raporcie należy szukać pól typu:

```text
status
final_operation_status
checkpoint_id
recovered_node_id
metrics_snapshot
```

### Clear faults

Czyści aktywne reguły fault injection.

Używaj tego przed kolejnym scenariuszem, żeby nie interpretować wyników na podstawie starych błędów.

---

## 8. Zakładka Fault injection

Zakładka **Fault injection** służy do kontrolowanego wprowadzania błędów.

### fault_type

Typ symulowanego błędu.

| Typ | Znaczenie |
|---|---|
| DROP | porzucanie wiadomości |
| DELAY | opóźnianie komunikatów |
| DUPLICATE | duplikowanie wiadomości |
| REPLAY | ponowne wysłanie starej wiadomości |
| EQUIVOCATION | zachowanie bizantyjskie: sprzeczne komunikaty |
| NETWORK_PARTITION | partycja sieci |
| LEADER_FAILURE | awaria lidera |

### protocol

Ogranicza błąd do konkretnego protokołu.

Przykłady:

| Protokół | Efekt |
|---|---|
| NARWHAL | problem dotyczy batchy i dostępności danych |
| HOTSTUFF | problem dotyczy proposal/vote/QC/commit |
| SWIM | problem dotyczy membership/failure detection |
| RECOVERY | problem dotyczy state transfer |

### message_kind

Ogranicza błąd do typu wiadomości.

Przykłady:

| Typ | Znaczenie |
|---|---|
| BATCH | wiadomość Narwhal z batchem |
| BATCH_ACK | potwierdzenie batcha |
| PROPOSAL | propozycja HotStuff |
| VOTE | głos repliki |
| COMMIT | commit |
| SWIM_PING | ping SWIM |
| SWIM_GOSSIP | gossip SWIM |
| STATE_TRANSFER | transfer stanu |

### source_node_id

Węzeł źródłowy, którego wiadomości mają być zaburzane.

Wartość `0` lub puste pole oznacza brak ograniczenia.

### target_node_id

Węzeł docelowy, którego wiadomości mają być zaburzane.

### probability

Prawdopodobieństwo wystąpienia błędu.

Przykłady:

| Wartość | Znaczenie |
|---|---|
| 0.0 | błąd nigdy nie występuje |
| 0.5 | błąd występuje średnio w połowie przypadków |
| 1.0 | błąd występuje zawsze |

### delay_ms

Opóźnienie w milisekundach dla typu `DELAY`.

### Add fault rule

Dodaje regułę błędu.

### Clear all faults

Usuwa wszystkie reguły błędów.

---

## 9. Zakładka Security / 2FA / transport

Zakładka pokazuje funkcje bezpieczeństwa.

### Transport status

Pokazuje status warstwy transportu, w tym informację o podpisywaniu wiadomości, replay protection i mTLS demo.

Należy podkreślić, że mTLS w projekcie jest demonstracyjne, a nie produkcyjne.

### gRPC runtime status

Pokazuje status kontraktu gRPC i runtime demo.

### TOTP setup

Generuje sekret TOTP i provisioning URI dla konta demo.

Przebieg:

1. Wpisz `account_name`, np. `demo@example.test`.
2. Kliknij **Setup TOTP**.
3. Skopiuj sekret lub provisioning URI do aplikacji TOTP.
4. Wygeneruj kod.
5. Wpisz kod w pole `code`.
6. Kliknij **Verify code**.

### Verify code

Sprawdza poprawność kodu TOTP.

Wynik:

```text
valid=True
```

oznacza poprawny kod.

---

# 10. Zakładka Sieć

Zakładka **Sieć** jest widokiem diagnostycznym dla klastra i demonstracyjnego chaina.

## 10.1. Tabela węzłów

Tabela pokazuje stan każdego node’a.

### Node

Numer węzła.

Przykład:

```text
1
2
3
4
5
6
```

### URL

Adres HTTP węzła z perspektywy hosta.

Przykład:

```text
http://localhost:8001
```

### Height

Wysokość lokalnego chaina.

Jeżeli klaster jest spójny, wszystkie poprawne węzły powinny mieć tę samą wysokość.

Przykład poprawny:

```text
node1 height = 4
node2 height = 4
node3 height = 4
node4 height = 4
node5 height = 4
node6 height = 4
```

Przykład błędny:

```text
node1 height = 689
node2 height = 19
node3 height = 689
```

Taki stan oznacza rozjazd replik.

### Last hash

Skrót ostatniego bloku.

Przy spójnym klastrze wszystkie poprawne węzły powinny mieć ten sam `last_hash`.

### Valid

Wynik weryfikacji chaina.

Typowe wartości:

| Wartość | Znaczenie |
|---|---|
| VALID | chain poprawny |
| INVALID | chain błędny |
| STALE | chain w starym formacie lub wymagający resetu |
| UNKNOWN | brak danych albo błąd odczytu |

### Faults

Lista wykrytych problemów.

Przykłady:

| Fault | Znaczenie |
|---|---|
| invalid_leader_sig | błędny podpis lidera |
| offline | węzeł niedostępny |
| byzantine | włączona symulacja błędu bizantyjskiego |
| slow | włączone opóźnienie |
| drop_rpc | porzucanie części komunikatów RPC |

---

## 10.2. Admin token

Pole tokenu administracyjnego.

Wypełnij tylko wtedy, gdy backend działa w trybie strict.

---

## 10.3. Odśwież stan klastra

Pobiera aktualny status wszystkich węzłów.

Używaj po każdej operacji:

```text
send transaction
mine/consensus
reset
fault injection
recovery
```

---

## 10.4. Uruchom konsensus (leader)

Wywołuje kopanie/commit przez lidera.

Typowy przepływ:

1. Wyślij transakcję testową.
2. Kliknij **Uruchom konsensus (leader)**.
3. Kliknij **Odśwież stan klastra**.
4. Sprawdź, czy height i last hash są zgodne na wszystkich node’ach.

---

## 10.5. Wyślij testową transakcję

Wysyła prostą operację testową do lidera.

Po wysłaniu transakcja trafia do mempoola. Sama transakcja nie musi jeszcze oznaczać wzrostu wysokości chaina. Wysokość wzrośnie po wykonaniu konsensusu/kopania.

---

## 10.6. Reset demo chain

Resetuje demonstracyjny chain.

Po ostatnich poprawkach reset powinien działać jako operacja klastrowa, gdy wywołujesz go z node1.

Zalecana procedura:

```bash
docker compose stop trafficgen
curl -X POST "http://127.0.0.1:8001/admin/network/reset-demo-chain?scope=cluster"
```

Po resecie oczekiwany stan:

```text
height = 0
verification_status = VALID
last_hash taki sam na wszystkich węzłach
```

---

## 10.7. Symulacja błędów dla wybranego węzła

Sekcja umożliwia ustawienie faultów dla konkretnego node’a.

### Węzeł

Wybór node’a, którego dotyczy konfiguracja.

### FAULT_OFFLINE

Symuluje wyłączenie węzła.

Efekt:

```text
węzeł przestaje poprawnie odpowiadać
SWIM może oznaczyć go jako SUSPECT albo DEAD
konsensus może działać dalej, jeśli quorum jest osiągalne
```

### FAULT_BYZANTINE

Symuluje zachowanie bizantyjskie.

Efekt:

```text
węzeł może głosować niezgodnie z poprawną logiką
system powinien zachować bezpieczeństwo, jeśli liczba błędnych węzłów mieści się w tolerancji
```

### FAULT_FLAPPING

Symuluje niestabilność węzła.

Węzeł raz działa, raz nie działa.

### FAULT_SLOW_MS

Dodaje opóźnienie odpowiedzi węzła.

Przykład:

```text
500 ms
1000 ms
3000 ms
```

### FAULT_FLAPPING_MOD

Parametr określający częstotliwość flappingu.

Im niższa wartość, tym częściej węzeł może zmieniać stan.

### FAULT_DROP_RPC_PROB

Prawdopodobieństwo porzucenia komunikatu RPC.

Przykład:

```text
0.00 = brak dropów
0.25 = około 25% komunikatów porzucanych
1.00 = wszystkie komunikaty porzucane
```

### Pobierz FAULT_* z węzła

Odczytuje aktualną konfigurację faultów z wybranego node’a.

### Zastosuj FAULT_* na węźle

Wysyła ustawioną konfigurację faultów do wybranego node’a.

---

## 10.8. Simulator ruchu

Sekcja steruje generatorem ruchu `trafficgen`.

### Ruch włączony

Jeśli zaznaczone, generator ruchu wysyła zapytania i transakcje testowe.

Do czystej prezentacji resetu i spójności chaina zalecane jest wyłączenie ruchu:

```bash
docker compose stop trafficgen
```

albo przez panel, jeśli dostępna jest kontrola `traffic_enabled`.

### Odśwież stan

Pobiera aktualny stan symulatora ruchu.

---

## 10.9. Szczegóły węzła

Pole szczegółów pokazuje wynik statusu i verify wybranego node’a.

To miejsce jest przydatne do diagnostyki błędów typu:

```text
invalid_leader_sig
previous_hash mismatch
node unreachable
chain stale
```

---

# 11. Scenariusze pokazania działania

## Scenariusz 1 — poprawne uruchomienie klastra i dashboardu

Cel: pokazać, że działa sześciowęzłowy klaster Docker.

Kroki:

```bash
docker compose down --remove-orphans
docker compose build --no-cache
docker compose up -d node1 node2 node3 node4 node5 node6
```

Uruchom GUI:

```bash
python VetClinic/GUI/run_bft_dashboard.py --base-url http://127.0.0.1:8001
```

W BFT Dashboard pokaż:

```text
Total nodes = 6
Quorum > 1
Current leader = node1 albo aktualny leader
Cluster nodes = ALIVE
```

W zakładce Sieć kliknij:

```text
Odśwież stan klastra
```

Oczekiwany wynik:

```text
wszystkie node’y odpowiadają
height taki sam albo po resecie równy 0
Valid = VALID
```

Ten scenariusz odpowiada kamieniowi milowemu dotyczącemu uruchomionego środowiska Docker Compose, replik i wstępnych warstw Narwhal/HotStuff.

---

## Scenariusz 2 — pełny przebieg operacji klienta przez BFT

Cel: pokazać proces logiczny: operacja klienta → Narwhal → HotStuff → commit → checkpoint/recovery.

Kroki w BFT Dashboard:

1. Wejdź w **Demo actions**.
2. Kliknij **Clear faults**.
3. Kliknij **Run full BFT demo**.
4. Otwórz **Open last report JSON**.
5. Przejdź do **Overview** i **Protocols**.
6. Przejdź do **Live logs**.

Co pokazać:

```text
Operation count rośnie
Narwhal batches rośnie
HotStuff proposals rośnie
QC count rośnie
Commit count rośnie
Checkpoint count rośnie
Recovery może pokazać transfer/recovered node
```

W **Live logs** pokaż kolejność:

```text
RECEIVED
BATCHED
PROPOSED
VOTED
COMMITTED
CHECKPOINTED
RECOVERED
```

Komentarz prezentacyjny:

```text
Operacja klienta nie jest wykonywana natychmiast lokalnie. Najpierw trafia do Narwhal, gdzie jest batchowana. Następnie HotStuff porządkuje ją przez proposal, vote, quorum certificate i commit. Po commicie stan może zostać zapisany w checkpoincie, a węzeł może być odtworzony przez recovery/state transfer.
```

Ten scenariusz jest bezpośrednio zgodny z opisem procesu logicznego w harmonogramie: przyjęcie operacji, batchowanie, proposal, głosy, quorum certificate, commit, aktualizacja stanu i checkpoint.

---

## Scenariusz 3 — demonstracja Narwhal

Cel: pokazać batchowanie i DAG.

Kroki:

1. Wyczyść błędy przez **Clear faults**.
2. Uruchom **Run full BFT demo**.
3. Przejdź do **Protocols**.
4. Obserwuj sekcję Narwhal.

Co pokazać:

```text
Narwhal batches
DAG batches
DAG tips
```

Komentarz:

```text
Narwhal odpowiada za warstwę dostępności danych. Operacje nie trafiają bezpośrednio do HotStuff, tylko są grupowane w batche. Dzięki temu konsensus nie musi przenosić pełnych danych operacji, tylko może pracować na referencjach do batchy.
```

---

## Scenariusz 4 — demonstracja HotStuff

Cel: pokazać proposal, vote, QC i commit.

Kroki:

1. Uruchom pełny demo flow.
2. Przejdź do **Protocols**.
3. Sprawdź pola HotStuff.
4. W **Live logs** ustaw filtr `HOTSTUFF`.

Co pokazać:

```text
HotStuff view
HotStuff leader
Proposals
QCs
Commits
```

Komentarz:

```text
HotStuff odpowiada za uzgodnienie kolejności operacji. Lider tworzy proposal, repliki głosują, a po osiągnięciu quorum powstaje QC. Commit oznacza, że operacja została zaakceptowana przez mechanizm konsensusu.
```

---

## Scenariusz 5 — demonstracja SWIM i awarii węzła

Cel: pokazać wykrywanie awarii i statusy membership.

Kroki w zakładce Sieć:

1. Wybierz np. `Node 3`.
2. Zaznacz `FAULT_OFFLINE`.
3. Kliknij **Zastosuj FAULT_* na węźle**.
4. Kliknij **Odśwież stan klastra**.

Kroki w BFT Dashboard:

1. Przejdź do **Protocols**.
2. Obserwuj `SWIM alive`, `SWIM suspect`, `SWIM dead`.
3. Przejdź do **Overview** i pokaż status badge node’a.

Oczekiwany efekt:

```text
node3 może przejść z ALIVE do SUSPECT albo DEAD
liczba alive spada
konsensus może nadal działać, jeśli quorum jest zachowane
```

Przywrócenie:

1. Odznacz `FAULT_OFFLINE`.
2. Kliknij **Zastosuj FAULT_* na węźle**.
3. Odśwież stan.
4. W razie potrzeby wykonaj reset klastra.

Komentarz:

```text
SWIM nie wykonuje konsensusu. Jego zadaniem jest obserwacja członkostwa klastra i wykrywanie awarii. Informacja o statusie węzła może wpływać na to, czy węzeł bierze udział w dalszym przetwarzaniu.
```

---

## Scenariusz 6 — opóźnienia i utrata komunikatów

Cel: pokazać odporność na błędy sieciowe.

Kroki w zakładce Sieć:

1. Wybierz `Node 4`.
2. Ustaw `FAULT_SLOW_MS = 1000`.
3. Ustaw `FAULT_DROP_RPC_PROB = 0.25`.
4. Kliknij **Zastosuj FAULT_* na węźle**.
5. Wyślij testową transakcję.
6. Kliknij **Uruchom konsensus (leader)**.
7. Odśwież stan klastra.

Co pokazać:

```text
czy height wzrósł na większości węzłów
czy Valid nadal jest VALID
czy któryś node ma fault w tabeli
czy logi pokazują opóźnienia/dropy
```

Komentarz:

```text
System powinien tolerować część błędów komunikacji. Jeżeli quorum pozostaje osiągalne, operacja może zostać zatwierdzona mimo opóźnień lub dropów.
```

Po scenariuszu:

```text
wyczyść fault
odśwież stan
ewentualnie wykonaj reset cluster
```

---

## Scenariusz 7 — zachowanie bizantyjskie

Cel: pokazać, że błędny węzeł nie powinien psuć poprawnego stanu klastra.

Kroki:

1. W zakładce Sieć wybierz `Node 5`.
2. Zaznacz `FAULT_BYZANTINE`.
3. Kliknij **Zastosuj FAULT_* na węźle**.
4. Wyślij testową transakcję.
5. Uruchom konsensus.
6. Odśwież stan klastra.
7. Sprawdź `Valid` i `Faults`.

Co pokazać:

```text
węzeł ma aktywny fault byzantine
pozostałe węzły powinny utrzymać poprawny stan
błędny podpis lub niespójna propozycja nie powinny być trwale zaakceptowane
```

Komentarz:

```text
To jest główny sens BFT: pojedynczy błędny lub złośliwy węzeł nie może samodzielnie narzucić błędnego stanu, jeśli liczba błędnych replik mieści się w założonej tolerancji.
```

---

## Scenariusz 8 — reset i spójność łańcucha

Cel: pokazać odzyskanie czystego, zgodnego stanu.

Kroki:

```bash
docker compose stop trafficgen
curl -X POST "http://127.0.0.1:8001/admin/network/reset-demo-chain?scope=cluster"
```

W zakładce Sieć:

1. Kliknij **Odśwież stan klastra**.
2. Sprawdź `Height`.
3. Sprawdź `Last hash`.
4. Sprawdź `Valid`.

Oczekiwany wynik:

```text
Height = 0 na wszystkich node’ach
Last hash taki sam na wszystkich node’ach
Valid = VALID
Faults puste albo brak błędów krytycznych
```

Komentarz:

```text
Reset musi być wykonany klastrowo, nie tylko lokalnie na node1. W przeciwnym razie node’y mogą mieć różne wysokości chaina, co prowadzi do rozjazdu stanu.
```

---

## Scenariusz 9 — checkpointing i recovery

Cel: pokazać mechanizm odtwarzania stanu po awarii.

Najprostszy przebieg:

1. W BFT Dashboard kliknij **Run full BFT demo**.
2. Przejdź do **Protocols**.
3. Pokaż sekcje `Checkpointing` i `Recovery`.
4. Otwórz **Open last report JSON**.

Co pokazać:

```text
Snapshots
Certificates
Transfers
Recovered nodes
checkpoint_id w raporcie
recovered_node_id w raporcie
```

Komentarz:

```text
Checkpoint zapisuje punkt kontrolny stanu. Recovery wykorzystuje checkpoint i state transfer, aby węzeł mógł nadrobić brakujący stan po awarii lub restarcie.
```

Ten scenariusz odpowiada części harmonogramu dotyczącej checkpointingu, state transfer i odtwarzania węzła po awarii.

---

## Scenariusz 10 — bezpieczeństwo: podpisy, replay protection, TOTP i gRPC

Cel: pokazać funkcje bezpieczeństwa.

Kroki:

1. Wejdź w **Security / 2FA / transport**.
2. Pokaż **Transport status**.
3. Pokaż **gRPC runtime status**.
4. Wykonaj **Setup TOTP**.
5. Wpisz kod TOTP.
6. Kliknij **Verify code**.
7. Uruchom **Run gRPC ping demo** w zakładce Demo actions.

Co powiedzieć:

```text
System podpisuje komunikaty i weryfikuje integralność. Replay protection ogranicza ponowne użycie starych komunikatów. gRPC pokazuje kontrakt komunikacji międzywęzłowej. TOTP demonstruje drugi składnik uwierzytelnienia dla operacji wymagających dodatkowego potwierdzenia.
```

---

# 12. Minimalna ścieżka prezentacji projektu

Jeżeli czas jest ograniczony, pokaż w tej kolejności:

1. **Start klastra**
   - `docker compose up -d node1 ... node6`
   - BFT Dashboard na `http://127.0.0.1:8001`
   - `Total nodes = 6`

2. **Overview**
   - liczba node’ów,
   - quorum,
   - leader,
   - statusy node’ów.

3. **Run full BFT demo**
   - pokaż raport JSON,
   - pokaż wzrost metryk.

4. **Protocols**
   - Narwhal batches,
   - HotStuff proposals/QC/commits,
   - SWIM alive/suspect/dead,
   - checkpoint/recovery.

5. **Live logs**
   - filtr `HOTSTUFF`,
   - filtr `NARWHAL`,
   - filtr `SWIM`.

6. **Fault injection**
   - dodaj `DELAY` albo `DROP`,
   - pokaż wpływ na logi i status.

7. **Zakładka Sieć**
   - pokaż height/hash/valid,
   - wyślij testową transakcję,
   - uruchom konsensus,
   - odśwież stan.

8. **Reset demo chain**
   - zatrzymaj trafficgen,
   - reset cluster,
   - pokaż powrót do `height = 0`, `VALID`.

9. **Security**
   - TOTP setup/verify,
   - gRPC ping demo,
   - transport status.

---

# 13. Typowe problemy i interpretacja

| Objaw | Przyczyna | Rozwiązanie |
|---|---|---|
| `Total nodes = 1` | dashboard podłączony do standalone API | użyj `http://127.0.0.1:8001` |
| `UNKNOWN` przy node’ach | brak danych SWIM albo zły target API | sprawdź Base URL i odśwież |
| `INVALID / invalid_leader_sig` | chain zawiera blok z błędnym podpisem albo stary stan DB | wykonaj reset cluster |
| różne `Height` między node’ami | rozjazd replik | zatrzymaj trafficgen i wykonaj reset cluster |
| fault nadal działa po scenariuszu | nie wyczyszczono reguł | kliknij Clear faults / Clear all faults |
| operacja nie dochodzi do commitu | brak quorum, fault, offline node albo drop RPC | usuń fault, sprawdź SWIM, resetuj stan |
| admin operation zwraca 401/403 | strict mode bez tokenu | wpisz Admin token |
| GUI pokazuje offline | backend nie działa albo zły port | sprawdź `docker ps` i Base URL |

---

# 14. Najważniejsza zasada interpretacyjna

Nie wystarczy patrzeć na jeden licznik. Poprawna prezentacja powinna zawsze zestawiać cztery widoki:

```text
Overview       → ogólny stan klastra
Protocols      → Narwhal / HotStuff / SWIM / checkpoint / recovery
Live logs      → dowód przebiegu komunikacji i zdarzeń
Sieć           → spójność chaina: height, hash, valid
```

Dopiero wtedy widać pełny sens projektu: nie tylko „aplikacja działa”, ale działa przepływ odpornego systemu rozproszonego zgodny z harmonogramem: membership, komunikacja, konsensus, błędy, checkpointing, recovery, security i obserwowalność.
