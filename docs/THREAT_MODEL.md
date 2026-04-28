# Threat model projektu

## Cel dokumentu

Ten dokument opisuje podstawowy model zagrozen dla calego projektu: VetClinic API, legacy blockchain/RPC/cluster/admin endpoints, BFT `/bft/*`, Docker Compose, monitoring, GUI, CI i zaleznosci. To fundament do kolejnych testow bezpieczenstwa i pentest scope.

Projekt dziala w trybie demonstracyjnym. Pokazuje mechanizmy BFT i obserwowalnosc, ale nie jest pelnym produkcyjnym hardeningiem. Docelowy tryb strict powinien blokowac endpointy administracyjne bez tokena i wymuszac wyrazne role operatora.

## Aktywa

- Dane uzytkownikow VetClinic: konta, role, dane kontaktowe i ustawienia uwierzytelniania.
- Dane zwierzat, wizyt, faktur i platnosci.
- Medical records oraz powiazane wpisy medyczne.
- Operacje BFT przyjmowane przez `/bft/client/submit`.
- Dane protokolow BFT: batch, proposal, vote, QC, checkpoint i state transfer.
- Klucze kryptograficzne demo oraz public key registry.
- Konfiguracja Docker Compose, Prometheus, Grafana i trafficgen.
- Sekrety lokalne, zmienne srodowiskowe, pliki `.env` i konfiguracja CI.

## Aktorzy

- anonymous user: niezalogowany klient probujacy odczytac lub zmodyfikowac dane.
- authenticated user: poprawnie zalogowany uzytkownik z normalnymi uprawnieniami.
- malicious user: uzytkownik probujacy IDOR/BOLA, eskalacji funkcji, masowego przypisania albo naduzycia zasobow.
- malicious node: wezel wysylajacy niepoprawne komunikaty BFT lub RPC.
- Byzantine proposer/voter: uczestnik HotStuff probujacy forged vote/proposal/checkpoint, equivocation albo replay.
- operator/admin: osoba zarzadzajaca konfiguracja, fault injection, monitoringiem i docker compose.

## Powierzchnie ataku

- `/bft/*`: operacje BFT, Narwhal, HotStuff, SWIM, fault injection, checkpointing, recovery, crypto i observability.
- `/admin/*`: funkcje administracyjne i panel stanu sieci.
- `/rpc/*`: komunikacja miedzy wezlami legacy.
- `/cluster/*`: konfiguracja i stan klastra.
- VetClinic CRUD endpoints: users, doctors, clients, animals, appointments, invoices, medical records.
- Blockchain endpoints: mempool, mining, chain verify i blockchain records.
- `/metrics`: metryki Prometheus.
- Docker Compose: ekspozycja portow, sekrety, konfiguracja Prometheus/Grafana, trafficgen.
- GUI PyQt: przeplywy logowania i operacje wykonywane przez klienta desktopowego.
- CI/dependencies: supply chain, workflow permissions, SCA/SAST, zaleznosci PyPI.

## Glowne zagrozenia

- IDOR/BOLA: dostep do zasobu przez zgadywanie identyfikatorow, np. cudze medical records, faktury albo wizyty.
- Broken authentication: slabe hasla, tokeny, reset hasla, sesje i brak sprawdzania tozsamosci.
- Broken function level authorization: dostep zwyklego uzytkownika do funkcji admin, cluster, fault injection lub recovery.
- Mass assignment: mozliwosc ustawienia pol, ktore powinny byc kontrolowane przez serwer, np. role, status platnosci, node status.
- Resource abuse: nadmierne tworzenie operacji, batchy, reguly fault injection, duze payloady albo kosztowne zapytania.
- Replay: ponowne uzycie podpisanego komunikatu BFT, glosu, checkpointu albo requestu state transfer.
- Equivocation: rozne proposal/vote od tego samego wezla w tym samym widoku.
- Forged vote/proposal/checkpoint: komunikaty z podrobionym podpisem lub nieznanym kluczem.
- State corruption: niespojny checkpoint, bledny hash stanu albo nieautoryzowany state transfer.
- Unauthorized fault injection: wlaczenie DROP/DELAY/partition przez nieuprawnionego aktora.
- Secret leakage: ujawnienie `.env`, tokenow, kluczy demo, konfiguracji SMTP/platnosci albo sekretow CI.
- Misconfiguration: otwarte porty, domyslne hasla Grafana, brak izolacji sieci, zbyt szerokie CORS, debug mode.

## OWASP API Security Top 10 2023

Plan testow odwoluje sie opisowo do OWASP API Security Top 10 2023. Szczegolnie istotne sa:

- BOLA: Broken Object Level Authorization, czyli IDOR na zasobach VetClinic i identyfikatorach BFT.
- Broken Authentication: bledy logowania, tokenow, resetu hasla i sesji.
- Broken Function Level Authorization: dostep do funkcji admin, cluster, RPC, fault injection i recovery.
- Unrestricted Resource Consumption: brak limitow payloadow, liczby operacji, batchy, requestow i metryk.
- Security Misconfiguration: niepoprawne ustawienia Docker Compose, monitoring, CORS, sekrety i workflow CI.

## VetClinic business logic

Domena VetClinic obejmuje uzytkownikow, lekarzy, zwierzeta, wizyty, medical records, faktury i platnosci. Glowne ryzyka to IDOR/BOLA na identyfikatorach zasobow, mass assignment pol takich jak `role`, `is_admin`, `is_superuser` i `is_paid`, brak walidacji kwot oraz odwolania do nieistniejacych `doctor_id`, `animal_id`, `owner_id` lub `invoice_id`.

W trybie demo czesc endpointow moze nie miec pelnego IAM. Testy security dokumentuja ten stan jako aktualne ograniczenie, ale wymagaja, aby API nie zwracalo 500 i nie ujawnialo danych ani stack trace.

## Blockchain/RPC legacy risk

Legacy blockchain, RPC i cluster endpoints obsluguja `/tx/*`, `/chain/*`, `/rpc/*` i `/peers`. Ryzyka obejmuja forged block proposal, forged signature, manipulacje mempoolem, naduzycie `/chain/mine_distributed`, ujawnienie topologii klastra oraz diagnostyke RPC bez kontroli dostepu.

Testy w tej warstwie sprawdzaja brak 500 dla niepoprawnych payloadow, brak wycieku sekretow i kontrolowane odpowiedzi dla mine/verify/status.

## SQL injection / ORM abuse

Projekt uzywa SQLAlchemy. Ryzyka obejmuja nieparametryzowany raw SQL, konkatenacje stringow SQL i f-stringi w `.execute()` lub `text()`. Testy dynamiczne wysylaja payloady typu `' OR 1=1 --`, a test statyczny skanuje kod API pod katem niebezpiecznych konstrukcji.

## Information leakage

Bledne requesty nie powinny ujawniac tracebackow, lokalnych sciezek plikow, `sqlalchemy.exc`, prywatnych kluczy, `LEADER_PRIV_KEY`, `BFT_ADMIN_TOKEN` ani innych sekretow. Dopuszczalne sa kontrolowane odpowiedzi 400, 401, 403, 404, 409 i 422.

## Decyzje projektowe

- Tryb demo pokazuje mechanizmy protokolowe bez pelnego hardeningu produkcyjnego.
- Tryb strict powinien blokowac endpointy administracyjne bez tokena.
- Testy deterministyczne pytest sa podstawowa warstwa kontroli regresji.
- Narzedzia Bandit, pip-audit, Semgrep, Trivy i ZAP sa dodatkowymi warstwami, nie zamiennikiem testow kontraktowych.
