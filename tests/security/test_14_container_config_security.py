from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_compose_and_api_dockerfile_exist() -> None:
    assert (ROOT / "docker-compose.yml").exists()
    assert (ROOT / "Dockerfile.api").exists()


def test_compose_avoids_high_risk_container_settings() -> None:
    compose = _read(ROOT / "docker-compose.yml").lower()
    assert "privileged: true" not in compose
    assert "network_mode: host" not in compose
    assert "/var/run/docker.sock" not in compose


def test_prometheus_and_grafana_ports_are_documented_as_local_demo() -> None:
    compose = _read(ROOT / "docker-compose.yml")
    assert "9090:9090" in compose
    assert "3000:3000" in compose

    docs = "\n".join(
        _read(path)
        for path in [ROOT / "README.md", ROOT / "docs" / "SECURITY_TEST_PLAN.md"]
        if path.exists()
    ).lower()
    assert "prometheus" in docs
    assert "grafana" in docs
    assert "demo" in docs
    assert "local" in docs


def test_api_dockerfile_avoids_remote_add_debug_and_root_runtime() -> None:
    dockerfile = _read(ROOT / "Dockerfile.api")
    lowered = dockerfile.lower()
    assert "add http://" not in lowered
    assert "add https://" not in lowered
    assert "debug=1" not in lowered
    assert "\nuser appuser" in lowered
