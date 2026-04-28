from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SECRET_MARKERS = [
    "LEADER_PRIV_KEY",
    "BFT_ADMIN_TOKEN",
    "private_key_b64",
]


def _response_text(response) -> str:
    return response.text.lower()


def test_env_file_is_not_committed_and_example_exists() -> None:
    assert not (ROOT / ".env").exists()
    assert (ROOT / ".env.example").exists()


def test_private_key_files_are_not_committed() -> None:
    forbidden = []
    for pattern in ("*.pem", "*.key", "id_rsa", "id_dsa"):
        forbidden.extend(
            path
            for path in ROOT.rglob(pattern)
            if ".git" not in path.parts and ".venv" not in path.parts
        )
    assert forbidden == []


def test_demo_keys_are_documented_as_demo_only() -> None:
    docs = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [ROOT / "README.md", ROOT / "docs" / "OGRANICZENIA.md"]
        if path.exists()
    ).lower()
    assert "demo" in docs
    assert "docker-compose" in docs or "docker compose" in docs
    assert "klucz" in docs or "key" in docs


def test_crypto_public_endpoints_do_not_expose_private_keys(security_bft_client) -> None:
    demo_keys = security_bft_client.post("/bft/crypto/demo-keys?total_nodes=6")
    assert demo_keys.status_code == 200
    assert "private_key_b64" not in _response_text(demo_keys)

    public_keys = security_bft_client.get("/bft/crypto/public-keys")
    assert public_keys.status_code == 200
    assert "private_key_b64" not in _response_text(public_keys)


def test_bft_status_does_not_leak_secret_markers(security_bft_client) -> None:
    response = security_bft_client.get("/bft/status")
    assert response.status_code != 500
    body = response.text
    for marker in SECRET_MARKERS:
        assert marker not in body
