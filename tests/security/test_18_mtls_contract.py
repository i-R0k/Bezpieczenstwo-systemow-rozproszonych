from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_mtls_documentation_and_tooling_files_exist() -> None:
    assert (ROOT / "docs" / "MTLS.md").exists()
    assert (ROOT / "scripts" / "generate_demo_certs.py").exists()
    assert (ROOT / "certs" / "README.md").exists()
    assert (ROOT / "docker-compose.override.tls.example.yml").exists()


def test_gitignore_protects_demo_cert_material() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8", errors="ignore")
    for pattern in (
        "certs/demo/*.key",
        "certs/demo/*.crt",
        "certs/demo/*.csr",
        "certs/demo/*.pem",
        "certs/demo/*.srl",
    ):
        assert pattern in gitignore


def test_transport_security_endpoint(security_bft_client) -> None:
    response = security_bft_client.get("/bft/security/transport")
    assert response.status_code == 200
    payload = response.json()
    assert payload["message_signing"] is True
    assert payload["replay_protection"] is True
    assert payload["mtls_runtime_enabled"] is False
    assert payload["demo_cert_tooling"] is True
    assert payload["docs"] == "docs/MTLS.md"
    assert "not enforced" in payload["limitation"]


def test_generate_demo_certs_help_returns_zero() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/generate_demo_certs.py", "--help"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert completed.returncode == 0
    assert "--nodes" in completed.stdout
    assert "--force" in completed.stdout


def test_generate_demo_certs_to_tmp_path(tmp_path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/generate_demo_certs.py",
            "--nodes",
            "2",
            "--out",
            str(tmp_path),
            "--force",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert completed.returncode == 0, completed.stderr
    for name in ("demo-ca.crt", "demo-ca.key", "node1.crt", "node1.key", "node2.crt", "node2.key", "client.crt", "client.key"):
        assert (tmp_path / name).exists()
    assert "PRIVATE KEY" not in completed.stdout
