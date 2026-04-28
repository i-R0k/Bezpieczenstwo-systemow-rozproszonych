# Automatyczny testbed BFT

## Cel

Testbed regresyjny sprawdza kontrakty etapow 1-6 BFT bez Dockera, bez uvicorn, bez Prometheus/Grafana i bez prawdziwej sieci. Testy uruchamiaja sie przez pytest i minimalna aplikacje FastAPI z samym routerem `/bft`.

## Struktura

```text
tests/bft/
  conftest.py
  test_01_architecture_contract.py
  test_02_operation_flow_contract.py
  test_03_narwhal_contract.py
  test_04_hotstuff_contract.py
  test_05_swim_contract.py
  test_06_full_bft_pipeline.py
  test_07_negative_paths.py
  test_08_router_contract.py
  test_09_full_app_smoke.py
  test_10_fault_injection_store.py
  test_11_fault_injection_service.py
  test_12_replay_guard.py
  test_13_equivocation_detector.py
  test_14_faults_narwhal_integration.py
  test_15_faults_hotstuff_integration.py
  test_16_faults_swim_integration.py
  test_17_fault_injection_router_contract.py
  test_18_checkpoint_recovery_contract.py
  test_25_crypto_keys.py
  test_26_crypto_envelope.py
  test_27_crypto_service.py
  test_28_crypto_narwhal_integration.py
  test_29_crypto_hotstuff_integration.py
  test_30_crypto_swim_integration.py
  test_31_crypto_checkpoint_recovery_integration.py
  test_32_crypto_router_contract.py
  test_33_observability_metrics.py
  test_34_observability_health.py
  test_35_demo_scenario_runner.py
  test_36_observability_router_contract.py
  test_37_metrics_no_duplicate_registration.py
  test_98_final_delivery_contract.py
  test_99_documentation_contract.py
```

## Zakres plikow

- `test_01_architecture_contract.py` - importy, enumy, quorum, event log, podstawowe endpointy architektury.
- `test_02_operation_flow_contract.py` - operacje, status transitions, trace, terminalne stany i router operacji.
- `test_03_narwhal_contract.py` - batch, DAG, ACK, certyfikat data availability i endpointy Narwhal.
- `test_04_hotstuff_contract.py` - proposal, vote, QC, commit, view-change i endpointy HotStuff.
- `test_05_swim_contract.py` - membership, ping, ping-req, gossip, recovery i integracja z HotStuff.
- `test_06_full_bft_pipeline.py` - pelny in-memory pipeline service/store oraz router.
- `test_07_negative_paths.py` - bledne sciezki, 404/409/400 i zakazana kolejnosc statusow.
- `test_08_router_contract.py` - smoke kontraktu routera bez oczekiwania zewnetrznych uslug.
- `test_09_full_app_smoke.py` - import pelnej aplikacji `vetclinic_api.main`, sprawdzenie rejestracji routera BFT i `GET /bft/architecture`.
- `test_10_fault_injection_store.py` - reguly, partycje, walidacja, counters i clear store.
- `test_11_fault_injection_service.py` - decyzje drop/delay/duplicate/replay/equivocation, filtry i partition.
- `test_12_replay_guard.py` - replay po `message_id` oraz brak podwojnego vote/commit.
- `test_13_equivocation_detector.py` - konflikty proposal w tym samym view/proposer oraz endpoint konfliktow.
- `test_14_faults_narwhal_integration.py` - drop batch, drop ACK, partition ACK i idempotentny duplicate ACK.
- `test_15_faults_hotstuff_integration.py` - drop proposal/vote/commit, leader failure, partition vote, replay vote i equivocation.
- `test_16_faults_swim_integration.py` - drop/delay ping, partition ping i drop gossip.
- `test_17_fault_injection_router_contract.py` - kontrakt endpointow `/bft/faults/*`.
- `test_18_checkpoint_recovery_contract.py` - snapshot, checkpoint certificate, state transfer, apply checkpoint i powrot wezla do `ALIVE`.
- `test_25_crypto_keys.py` - Ed25519 keypair, podpisy, registry i publiczny widok kluczy.
- `test_26_crypto_envelope.py` - canonical JSON, stabilny `message_id`, podpis obejmujacy nonce/body.
- `test_27_crypto_service.py` - sign/verify, replay, invalid signature, protocol/kind mismatch i EventLog.
- `test_28_crypto_narwhal_integration.py` - podpisane `BATCH` i `BATCH_ACK`.
- `test_29_crypto_hotstuff_integration.py` - podpisane proposal/vote, replay signed vote i QC.
- `test_30_crypto_swim_integration.py` - podpisane ping/ack/gossip i invalid gossip signature.
- `test_31_crypto_checkpoint_recovery_integration.py` - podpisane checkpoint/state transfer i recovery.
- `test_32_crypto_router_contract.py` - endpointy `/bft/crypto/*` i replay przez drugi verify.
- `test_33_observability_metrics.py` - eksport Prometheus, mapping EventLog -> counters i gauges.
- `test_34_observability_health.py` - health check komponentow i ostrzezenia dla pustego SWIM/crypto.
- `test_35_demo_scenario_runner.py` - automatyczne demo koncowe bez sieci i Dockera.
- `test_36_observability_router_contract.py` - endpointy health/metrics/demo.
- `test_37_metrics_no_duplicate_registration.py` - brak duplicate timeseries przy wielu importach/instancjach.
- `test_98_final_delivery_contract.py` - finalny kontrakt demo, raportu, health, metrics i trace `EXECUTED`.
- `test_99_documentation_contract.py` - smoke test README i dokumentow koncowych projektu.

## Minimalny router a full app smoke

Wiekszosc testbedu uzywa minimalnej aplikacji FastAPI z samym routerem `/bft`. Dzieki temu testy sa szybkie, izolowane i nie dotykaja bazy ani routerow domenowych.

`test_09_full_app_smoke.py` jest osobnym bezpiecznikiem. Importuje pelne `vetclinic_api.main`, pozwala na lokalne side effecty typu utworzenie tabel SQLite i sprawdza, czy router BFT jest faktycznie zarejestrowany w glownej aplikacji. Ten test ma wykrywac regresje integracji routerow, ktorych minimalny testbed nie zobaczy.

## Uruchamianie

```powershell
python -m pytest tests/bft -q
python scripts/run_bft_testbed.py
make test-bft
make test-bft-contract
```

## Interpretacja porazek

Porazka testu kontraktowego oznacza regresje publicznego API albo modelu protokolu. Porazka testu integracyjnego zwykle oznacza niespojnosc przejsc statusow miedzy Narwhal, HotStuff i SWIM. Nie nalezy ukrywac takich porazek przez `skip`; trzeba naprawic implementacje albo jawnie zmienic kontrakt.

Fault injection jest testowany bez sieci i bez `sleep`. `DELAY` zapisuje symulowany delay w `FaultDecision` albo eventach, a `DROP`/partycje blokuja lokalna sciezke service/router tak samo, jak zrobilby to przyszly transport.

Testy crypto sprawdzaja replay protection przez ponowna weryfikacje tego samego `BftSignedMessage` oraz invalid signature przez zmiane podpisu/body/nonce. Nie wymagaja zewnetrznego PKI ani mTLS.

Demo scenario runner wykonuje pelny happy path koncowy i zwraca `BftDemoReport`. Scenariusz obejmuje Narwhal, HotStuff, SWIM, fault injection, checkpointing, recovery, crypto verification i snapshot metryk.

Final delivery contract dopina punkt 10 projektu. Sprawdza `POST /bft/demo/run`, `GET /bft/demo/last-report`, health, metrics, architecture, trace operacji z `EXECUTED`, checkpoint, recovered node i snapshot metryk.

## Zasady rozbudowy

- Punkt 6 fault injection: testy 10-17 waliduja store, service, replay, equivocation, integracje z Narwhal/HotStuff/SWIM i router.
- Punkt 7 checkpointing/state transfer: dodac testy snapshotow, recovery i zgodnosci statusu `RECOVERING`.
- Punkt 7 checkpointing/state transfer: test 18 waliduje kontrakt snapshotu, certyfikatu i recovery.
- Punkt 8 crypto/mTLS/replay protection: dodac testy podpisow, nonce i odrzucenia replay.
- Punkt 8 crypto/mTLS/replay protection: testy 25-32 waliduja Ed25519, canonical JSON, envelope, replay i integracje protokolow.
- Punkt 9 monitoring/demo: dodac testy metryk i endpointow diagnostycznych bez zewnetrznego Prometheusa.
- Punkt 9 monitoring/demo: testy 33-37 waliduja metryki, health endpointy i demo runner.
- Punkt 10 dokumentacja koncowa: testy 98-99 waliduja finalny kontrakt demo i komplet dokumentacji.
