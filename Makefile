.PHONY: help
help:
	@echo "Dostepne cele:"
	@echo "  make cluster-up              - build i uruchomienie docker compose"
	@echo "  make cluster-down            - zatrzymanie docker compose"
	@echo "  make test                    - uruchomienie wszystkich testow pytest"
	@echo "  make test-bft                - uruchomienie tests/bft"
	@echo "  make test-bft-contract       - uruchomienie scripts/run_bft_testbed.py"
	@echo "  make test-bft-faults         - testy fault injection"
	@echo "  make test-bft-recovery       - testy checkpointing/recovery"
	@echo "  make test-bft-crypto         - testy crypto/replay protection"
	@echo "  make test-bft-observability  - testy observability/demo"
	@echo "  make test-bft-final          - testy final delivery, dokumentacji i harmonogramu"
	@echo "  make test-security           - uruchomienie tests/security"
	@echo "  make test-security-contract  - uruchomienie scripts/run_security_testbed.py"
	@echo "  make test-security-api       - smoke test API security"
	@echo "  make test-security-bft       - BFT protocol attack security tests"
	@echo "  make test-security-legacy    - legacy blockchain/RPC/cluster/admin security"
	@echo "  make test-security-infra     - secrets, containers, monitoring, GUI, mTLS, SAST/SCA contracts"
	@echo "  make security-tools          - pytest security + Bandit/pip-audit/Semgrep/Trivy wrapper"
	@echo "  make generate-demo-certs     - generate local demo TLS/mTLS certificates"
	@echo "  make pentest-quick           - local-only quick DAST harness"
	@echo "  make pentest-zap             - local-only quick harness plus ZAP baseline"
	@echo "  make pentest-full            - local-only full DAST harness with optional tools"
	@echo "  make pentest-nuclei          - local-only Nuclei templates only, if nuclei is installed"
	@echo "  make test-pentest            - pentest harness contract tests"
	@echo "  make run-bft-dashboard       - uruchomienie PyQt BFT Dashboard"
	@echo "  make test-gui                - testy kontraktowe GUI"
	@echo "  make test-all                - testy BFT/security/pentest/GUI"
	@echo "  make lint                    - ruff + mypy + bandit, jesli sa dostepne"
	@echo "  make scenario-healthy        - scenariusz: wszyscy zdrowi"
	@echo "  make scenario-faults1        - scenariusz: offline + slow"
	@echo "  make scenario-faults2        - scenariusz: 2 byzantine"
	@echo "  make scenario-faults3        - scenariusz: 3 byzantine"

.PHONY: cluster-up
cluster-up:
	docker compose up --build

.PHONY: cluster-down
cluster-down:
	docker compose down

.PHONY: test
test:
	python -m pytest

.PHONY: test-all
test-all:
	python -m pytest tests/bft tests/security tests/pentest tests/gui -q

.PHONY: test-bft
test-bft:
	python -m pytest tests/bft -q

.PHONY: test-bft-contract
test-bft-contract:
	python scripts/run_bft_testbed.py

.PHONY: test-bft-faults
test-bft-faults:
	python -m pytest tests/bft/test_10_fault_injection_store.py tests/bft/test_11_fault_injection_service.py tests/bft/test_12_replay_guard.py tests/bft/test_13_equivocation_detector.py tests/bft/test_14_faults_narwhal_integration.py tests/bft/test_15_faults_hotstuff_integration.py tests/bft/test_16_faults_swim_integration.py tests/bft/test_17_fault_injection_router_contract.py -q

.PHONY: test-bft-recovery
test-bft-recovery:
	python -m pytest tests/bft/test_18_checkpoint_recovery_contract.py tests/bft/test_31_crypto_checkpoint_recovery_integration.py -q

.PHONY: test-bft-crypto
test-bft-crypto:
	python -m pytest tests/bft/test_25_crypto_keys.py tests/bft/test_26_crypto_envelope.py tests/bft/test_27_crypto_service.py tests/bft/test_28_crypto_narwhal_integration.py tests/bft/test_29_crypto_hotstuff_integration.py tests/bft/test_30_crypto_swim_integration.py tests/bft/test_31_crypto_checkpoint_recovery_integration.py tests/bft/test_32_crypto_router_contract.py -q

.PHONY: test-bft-observability
test-bft-observability:
	python -m pytest tests/bft/test_33_observability_metrics.py tests/bft/test_34_observability_health.py tests/bft/test_35_demo_scenario_runner.py tests/bft/test_36_observability_router_contract.py tests/bft/test_37_metrics_no_duplicate_registration.py tests/bft/test_102_dashboard_communication_contract.py -q

.PHONY: test-bft-final
test-bft-final:
	python -m pytest tests/bft/test_98_final_delivery_contract.py tests/bft/test_99_documentation_contract.py tests/bft/test_101_grpc_contract.py tests/bft/test_102_dashboard_communication_contract.py tests/bft/test_103_schedule_full_compliance_contract.py tests/bft/test_104_grpc_runtime_demo.py -q

.PHONY: test-security
test-security:
	python -m pytest tests/security -q

.PHONY: test-security-contract
test-security-contract:
	python scripts/run_security_testbed.py

.PHONY: test-security-api
test-security-api:
	python -m pytest tests/security/test_01_api_authentication.py tests/security/test_02_api_authorization.py tests/security/test_03_api_input_validation.py tests/security/test_04_vetclinic_business_logic.py tests/security/test_05_sqlalchemy_sqli_contract.py tests/security/test_15_error_handling_information_leakage.py tests/security/test_16_resource_abuse_dos_limits.py tests/security/test_19_totp_2fa_contract.py tests/security/test_20_dashboard_exposure_security.py tests/security/test_21_grpc_runtime_security.py -q

.PHONY: test-security-bft
test-security-bft:
	python -m pytest tests/security/test_08_bft_protocol_security.py tests/security/test_09_crypto_replay_equivocation.py tests/security/test_10_checkpoint_recovery_security.py tests/security/test_11_fault_injection_abuse_security.py tests/security/test_12_swim_membership_security.py -q

.PHONY: test-security-legacy
test-security-legacy:
	python -m pytest tests/security/test_06_blockchain_rpc_security.py tests/security/test_07_admin_cluster_security.py -q

.PHONY: test-security-infra
test-security-infra:
	python -m pytest tests/security/test_13_secrets_config_contract.py tests/security/test_14_container_config_security.py tests/security/test_15_monitoring_exposure.py tests/security/test_16_gui_static_security.py tests/security/test_17_sast_sca_wrappers.py tests/security/test_18_mtls_contract.py -q

.PHONY: security-tools
security-tools:
	python scripts/run_security_tools.py

.PHONY: generate-demo-certs
generate-demo-certs:
	python scripts/generate_demo_certs.py --nodes 6 --out certs/demo --force

.PHONY: pentest-quick
pentest-quick:
	python scripts/run_pentest_local.py --quick

.PHONY: pentest-zap
pentest-zap:
	python scripts/run_pentest_local.py --quick --zap

.PHONY: pentest-full
pentest-full:
	python scripts/run_pentest_local.py --full

.PHONY: pentest-nuclei
pentest-nuclei:
	python scripts/run_pentest_local.py --nuclei-only

.PHONY: test-pentest
test-pentest:
	python -m pytest tests/pentest -q

.PHONY: run-bft-dashboard
run-bft-dashboard:
	python VetClinic/GUI/run_bft_dashboard.py

.PHONY: test-gui
test-gui:
	python -m pytest tests/gui -q

.PHONY: lint
lint:
	ruff VetClinic/API/vetclinic_api || true
	mypy VetClinic/API/vetclinic_api || true
	bandit -r VetClinic/API/vetclinic_api || true

.PHONY: scenario-healthy
scenario-healthy:
	python -m scripts.cluster_scenarios healthy

.PHONY: scenario-faults1
scenario-faults1:
	python -m scripts.cluster_scenarios faults_offline_slow

.PHONY: scenario-faults2
scenario-faults2:
	python -m scripts.cluster_scenarios faults_byzantine_2

.PHONY: scenario-faults3
scenario-faults3:
	python -m scripts.cluster_scenarios faults_byzantine_3
