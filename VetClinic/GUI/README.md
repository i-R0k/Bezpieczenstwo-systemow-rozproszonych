# PyQt BFT Dashboard

Desktopowy dashboard BFT jest glowna warstwa prezentacyjna dla protokolow Narwhal, HotStuff, SWIM, recovery, fault injection, gRPC demo i 2FA/TOTP. Jest dostepny jako osobna aplikacja oraz jako zakladka `BFT Dashboard` w panelu administratora VetClinic.

## Backend

```powershell
cd VetClinic/API
$env:PYTHONPATH="."
uvicorn vetclinic_api.main:app --reload
```

Domyslny URL backendu to `http://127.0.0.1:8000`.

## Dashboard standalone

```powershell
python VetClinic/GUI/run_bft_dashboard.py
python VetClinic/GUI/run_bft_dashboard.py --base-url http://127.0.0.1:8000
```

`requirements-gui.txt` instaluje PyQt5 jako stabilny fallback. Kod dashboardu uzywa PyQt6, jesli jest juz dostepny w srodowisku projektu, a w przeciwnym razie przechodzi na PyQt5.

Strict mode z tokenem admina:

```powershell
$env:BFT_SECURITY_MODE="strict"
$env:BFT_ADMIN_TOKEN="change-me"
python VetClinic/GUI/run_bft_dashboard.py --admin-token change-me
```

## Panel administratora

W glownym GUI VetClinic wybierz role `Administrator`, a potem zakladke `BFT Dashboard`. Zakladka korzysta z `BFT_DASHBOARD_BASE_URL` albo domyslnie z `http://127.0.0.1:8000`.

## Co pokazac na prezentacji

- `Run full BFT demo`
- `Run gRPC ping demo`
- `Fault injection`: dodanie `DROP` dla `VOTE` albo `SWIM_PING`
- `Live logs`: communication log i recent events
- `Security / 2FA / transport`: gRPC runtime, mTLS status, TOTP setup/verify
- `Protocols`: Narwhal, HotStuff, SWIM oraz checkpoint/recovery
