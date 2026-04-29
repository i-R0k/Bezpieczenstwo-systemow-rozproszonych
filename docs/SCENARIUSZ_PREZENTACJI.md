# Scenariusz prezentacji

Ten przebieg jest przygotowany na okolo 15 minut. Kolejnosc pokazuje najpierw zgodnosc z harmonogramem i testy, a potem wybrane endpointy demonstracyjne.

## 1. Repo i README

Cel: pokazac, ze README jest glownym landing page projektu.

Pokaz:

```text
README.md
```

Co powiedziec prowadzacemu: projekt sklada sie z demonstratora BFT, starszej domeny VetClinic, security tests i lokalnego pentest harness. README prowadzi do dokumentow szczegolowych.

## 2. Harmonogram

Cel: pokazac jawne mapowanie wymagan na implementacje.

Pokaz:

```text
docs/ZGODNOSC_Z_HARMONOGRAMEM.md
```

Oczekiwany wynik: tabela ma status dla kazdego obszaru, w tym gRPC, mTLS, 2FA, GUI, komunikacji miedzy procesami i pentestu.

Co powiedziec prowadzacemu: elementy kontraktowe albo demonstracyjne nie sa opisane jako produkcyjne; gRPC runtime i produkcyjne mTLS sa oznaczone jako ograniczone.

## 3. BFT testbed

Cel: pokazac powtarzalne testy bez Dockera.

Komenda:

```powershell
python scripts/run_bft_testbed.py
```

Oczekiwany wynik: runner wypisuje sekcje testow, w tym `[103] Schedule full compliance contract`, a pytest konczy sie sukcesem.

## 4. Security testbed

Cel: pokazac testy bezpieczenstwa calego projektu.

Komenda:

```powershell
python scripts/run_security_testbed.py
```

Oczekiwany wynik: testy security przechodza lokalnie bez Dockera i uvicorn.

## 5. Pentest quick

Cel: pokazac lokalny, kontrolowany harness pentestowy.

Komenda:

```powershell
python scripts/run_pentest_local.py --quick
```

Oczekiwany wynik: skrypt uruchamia lekkie probe HTTP dla localhost i zapisuje raport w `reports/pentest/<timestamp>/`.

Co powiedziec prowadzacemu: harness ma blokade localhost-only i nie sluzy do skanowania cudzych hostow.

## 6. Status BFT

Cel: pokazac zagregowany stan systemu.

Endpoint:

```text
GET /bft/status
```

Oczekiwany wynik: odpowiedz zawiera podsumowanie architektury, quorum, Narwhal, HotStuff, SWIM, fault injection, checkpointing, recovery, crypto i observability.

## 7. Demo koncowe API

Cel: pokazac pelny happy path przez jeden endpoint.

Endpointy:

```text
POST /bft/demo/run
GET  /bft/demo/last-report
```

Oczekiwany wynik: raport ma `status=ok`, `final_operation_status=EXECUTED`, `checkpoint_id`, `recovered_node_id` i `metrics_snapshot`.

## 8. Dashboard

Cel: pokazac prosta wizualizacje topologii, membership, konsensusu, recovery i zdarzen.

Endpoint:

```text
GET /bft/dashboard
```

Oczekiwany wynik: HTML dashboard pokazuje Cluster nodes, SWIM membership, HotStuff, Narwhal, fault injection, checkpoint/recovery, crypto/security, recent events i communication log.

Co powiedziec prowadzacemu: dashboard korzysta z polling/fetch i logicznego `EventLog`, a nie z WebSocket ani packet capture.

## Prezentacja przez PyQt BFT Dashboard

Cel: pokazac glowna desktopowa warstwe prezentacyjna projektu.

Kroki:

1. Uruchom backend:

```powershell
cd VetClinic/API
$env:PYTHONPATH="."
uvicorn vetclinic_api.main:app --reload
```

2. Uruchom PyQt dashboard:

```powershell
python VetClinic/GUI/run_bft_dashboard.py
```

3. Kliknij `Connect/Test`.
4. Kliknij `Run full BFT demo`.
5. Pokaz `Overview` i `Protocols`.
6. Pokaz `Live logs`.
7. Dodaj fault `DROP` dla `VOTE` albo `SWIM_PING`.
8. Pokaz wplyw na HotStuff/SWIM.
9. Kliknij `Clear faults`.
10. Kliknij `Run gRPC ping demo`.
11. Pokaz `Security / 2FA / transport` i wykonaj TOTP setup/verify.
12. Pokaz recovery/checkpoint w zakladce `Protocols`.

Co powiedziec prowadzacemu: PyQt BFT Dashboard jest wpiety rowniez w panel admina VetClinic jako zakladka `BFT Dashboard`; HTML `/bft/dashboard` zostal tylko jako lekki fallback.

## 9. gRPC i .proto

Cel: pokazac domkniecie punktu harmonogramu dotyczacego kontraktu transportowego.

Pokaz:

```text
proto/bft.proto
GET /bft/grpc/contract
```

Oczekiwany wynik: `.proto` zawiera `BftNodeService`, a endpoint zwraca `implementation_level=contract-only`.

Co powiedziec prowadzacemu: podstawowa sciezka wykonania nadal dziala przez FastAPI/in-memory; pelny runtime gRPC jest kierunkiem rozwoju.

## 10. 2FA/TOTP

Cel: pokazac minimalny flow 2FA bez przebudowy modelu uzytkownikow.

Endpointy:

```text
POST /security/2fa/demo/setup
POST /security/2fa/demo/verify
```

Oczekiwany wynik: setup zwraca `secret` i `otpauth://` provisioning URI, a verify rozroznia poprawny i bledny kod TOTP.

## 11. Certyfikaty TLS/mTLS

Cel: pokazac tooling certyfikatow demo.

Komenda:

```powershell
python scripts/generate_demo_certs.py --nodes 2 --out /tmp/bsr-certs --force
```

Oczekiwany wynik: powstaje demo CA oraz certyfikaty node1 i node2 w katalogu wyjsciowym.

Co powiedziec prowadzacemu: runtime domyslny nie wymusza mTLS; repo zawiera dokumentacje, generator certyfikatow i przyklad TLS.

## 12. Ograniczenia

Cel: pokazac uczciwy zakres projektu.

Pokaz:

```text
docs/OGRANICZENIA.md
```

Co powiedziec prowadzacemu: ograniczenia sa jawne: in-memory state, brak pelnego runtime gRPC, brak produkcyjnego mTLS, uproszczone 2FA, logiczna komunikacja miedzy wezlami i demonstracyjne Narwhal/HotStuff/SWIM.
