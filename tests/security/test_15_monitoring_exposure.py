from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SECRET_TERMS = [
    "private_key",
    "leader_priv_key",
    "bft_admin_token",
    "stripe",
    "jwt secret",
]


def _assert_no_secret_terms(text: str) -> None:
    lowered = text.lower()
    for term in SECRET_TERMS:
        assert term not in lowered


def test_bft_metrics_and_health_do_not_expose_secret_terms(security_bft_client) -> None:
    metrics = security_bft_client.get("/bft/observability/metrics")
    assert metrics.status_code == 200
    _assert_no_secret_terms(metrics.text)

    health = security_bft_client.get("/bft/observability/health")
    assert health.status_code == 200
    _assert_no_secret_terms(health.text)


def test_prometheus_config_does_not_contain_secrets() -> None:
    prometheus = ROOT / "prometheus" / "prometheus.yml"
    assert prometheus.exists()
    _assert_no_secret_terms(prometheus.read_text(encoding="utf-8", errors="ignore"))


def test_grafana_provisioning_does_not_contain_non_demo_passwords() -> None:
    grafana_root = ROOT / "Grafana"
    assert grafana_root.exists()
    findings = []
    for path in grafana_root.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            if "password" in text and "demo" not in text:
                findings.append(str(path.relative_to(ROOT)))
            _assert_no_secret_terms(text)
    assert findings == []


def test_monitoring_exposure_is_documented_as_local_demo() -> None:
    docs = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [ROOT / "README.md", ROOT / "docs" / "SECURITY_TEST_PLAN.md"]
        if path.exists()
    ).lower()
    assert "prometheus" in docs
    assert "grafana" in docs
    assert "local" in docs
    assert "demo" in docs
