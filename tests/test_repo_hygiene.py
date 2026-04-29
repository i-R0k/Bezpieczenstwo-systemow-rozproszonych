from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _tracked_files() -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return [ROOT / line for line in completed.stdout.splitlines() if line.strip()]


def test_gitignore_is_clean_and_complete() -> None:
    content = _read(".gitignore")
    assert "contentReference" not in content
    assert "oaicite" not in content
    for entry in [
        "__pycache__/",
        "*.py[cod]",
        ".pytest_cache/",
        ".mypy_cache/",
        ".ruff_cache/",
        ".coverage",
        "htmlcov/",
        ".venv/",
        ".env",
        "*.env",
        "reports/**",
        "pentest/reports/**",
        ".generated_grpc/",
        "certs/demo/*",
        "build/",
        "dist/",
        "*.egg-info/",
    ]:
        assert entry in content


def test_requirements_are_normalized() -> None:
    api = _read("requirements-api.txt")
    full = _read("requirements.txt")
    assert "Requests==" not in api
    assert "Requests==" not in full
    if "pydantic[email]" in api:
        assert "email-validator" not in {
            line.strip()
            for line in api.splitlines()
            if line.strip() and not line.strip().startswith("#")
        }
    assert "grpcio" in api
    assert "pyotp" in api
    assert "prometheus-client" in api


def test_package_markers_and_layout_document_exist() -> None:
    assert (ROOT / "VetClinic" / "__init__.py").exists()
    assert (ROOT / "VetClinic" / "GUI" / "__init__.py").exists()
    assert (ROOT / "docs" / "REPO_LAYOUT.md").exists()


def test_no_tracked_generated_trash() -> None:
    forbidden_names = {"__pycache__", ".pytest_cache", ".DS_Store"}
    forbidden_suffixes = {".pyc", ".log"}
    offenders: list[str] = []
    for path in _tracked_files():
        parts = set(path.relative_to(ROOT).parts)
        if parts & forbidden_names or path.suffix in forbidden_suffixes:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []


def test_no_private_demo_certs_are_present() -> None:
    certs_dir = ROOT / "certs" / "demo"
    allowed = {".gitkeep", "README.md"}
    offenders = [
        path.name
        for path in certs_dir.glob("*")
        if path.name not in allowed and path.suffix.lower() in {".key", ".pem", ".crt", ".csr", ".srl"}
    ]
    assert offenders == []


def test_report_directories_contain_only_gitkeep() -> None:
    for relative in ["pentest/reports", "reports"]:
        directory = ROOT / relative
        if not directory.exists():
            continue
        offenders = [
            str(path.relative_to(ROOT))
            for path in directory.rglob("*")
            if path.is_file() and path.name != ".gitkeep"
        ]
        assert offenders == []


def test_makefile_help_matches_required_targets() -> None:
    makefile = _read("Makefile")
    targets = [
        "test-bft",
        "test-security",
        "test-pentest",
        "test-gui",
        "test-all",
        "run-bft-dashboard",
        "pentest-quick",
        "security-tools",
        "generate-demo-certs",
    ]
    for target in targets:
        assert f"make {target}" in makefile
        assert f"{target}:" in makefile
