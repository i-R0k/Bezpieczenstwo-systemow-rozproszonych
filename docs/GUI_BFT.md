# PyQt BFT Dashboard

Harmonogram projektu obejmowal GUI do wizualizacji topologii, rund konsensusu, zdarzen systemowych, membership i recovery. Glowna warstwa prezentacyjna to teraz desktopowy **PyQt BFT Dashboard**.

## Implementacja

- `VetClinic/GUI/bft_dashboard.py` - glowne okno `BftDashboardWindow` oraz widget `BftDashboardWidget`;
- `VetClinic/GUI/bft_api_client.py` - synchroniczny klient API dla `/bft/*` i `/security/2fa/demo/*`;
- `VetClinic/GUI/bft_widgets.py` - karty metryk, status badges, tabele logow i dialog JSON;
- `VetClinic/GUI/run_bft_dashboard.py` - samodzielne uruchomienie dashboardu;
- `VetClinic/GUI/vetclinic_gui/windows/Admin/bft_dashboard_widget.py` - wpiecie w panel administratora VetClinic;
- `GET /bft/dashboard` - lekki HTML fallback pozostawiony dla kompatybilnosci.

## Zakladki

Dashboard PyQt pokazuje:

- `Overview` - nodes, quorum, leader, view, operacje, batch, QC, commity, checkpointy i faults;
- `Protocols` - Narwhal DAG, HotStuff view/QC/commit, SWIM membership, checkpoint/recovery;
- `Live logs` - communication log i recent events z filtrem protokolu;
- `Demo actions` - `Run full BFT demo`, `Run gRPC ping demo`, refresh i clear faults;
- `Fault injection` - formularz reguly DROP/DELAY/DUPLICATE/REPLAY/EQUIVOCATION/NETWORK_PARTITION/LEADER_FAILURE;
- `Security / 2FA / transport` - mTLS status, gRPC runtime status i TOTP setup/verify.

## Uruchomienie

Backend:

```powershell
cd VetClinic/API
$env:PYTHONPATH="."
uvicorn vetclinic_api.main:app --reload
```

Dashboard:

```powershell
python VetClinic/GUI/run_bft_dashboard.py
python VetClinic/GUI/run_bft_dashboard.py --base-url http://127.0.0.1:8000
```

Strict mode:

```powershell
$env:BFT_SECURITY_MODE="strict"
$env:BFT_ADMIN_TOKEN="change-me"
python VetClinic/GUI/run_bft_dashboard.py --admin-token change-me
```

Panel administratora: uruchom glowne GUI VetClinic, wybierz role `Administrator`, a potem zakladke `BFT Dashboard`.

## Scenariusz prezentacji

1. Uruchom backend FastAPI.
2. Uruchom PyQt dashboard albo wejdz w zakladke `BFT Dashboard` w panelu admina.
3. Kliknij `Connect/Test`.
4. Kliknij `Run full BFT demo`.
5. Pokaz `Overview` i `Protocols`.
6. Pokaz `Live logs`.
7. Dodaj fault `DROP` dla `VOTE` albo `SWIM_PING`.
8. Pokaz wplyw na HotStuff/SWIM i log komunikacji.
9. Kliknij `Clear faults`.
10. Kliknij `Run gRPC ping demo`.
11. Pokaz TOTP setup/verify.
12. Pokaz checkpoint/recovery.

## Ograniczenia

- Dashboard jest demonstracyjny i korzysta z lokalnego FastAPI `http://127.0.0.1:8000`.
- Auto-refresh uzywa okresowego polling, bez WebSocket.
- Communication log jest logicznym widokiem `EventLog`, a nie packet capture.
- HTML `/bft/dashboard` pozostaje lekkim fallbackiem, ale nie jest glowna warstwa prezentacyjna.
