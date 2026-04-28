from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore").lower()


def test_security_requirements_and_workflow_exist() -> None:
    assert (ROOT / "requirements-security.txt").exists()
    assert (ROOT / ".github" / "workflows" / "security-tests.yml").exists()


def test_security_workflow_runs_pytest_bandit_and_pip_audit() -> None:
    workflow = _read(ROOT / ".github" / "workflows" / "security-tests.yml")
    assert "pytest tests/security" in workflow
    assert "bandit" in workflow
    assert "pip-audit" in workflow


def test_optional_semgrep_and_trivy_are_non_blocking_in_workflow() -> None:
    workflow = _read(ROOT / ".github" / "workflows" / "security-tests.yml")
    if "semgrep" in workflow:
        assert "continue-on-error: true" in workflow
    if "trivy" in workflow:
        assert "continue-on-error: true" in workflow


def test_local_security_tools_are_documented() -> None:
    docs = "\n".join(
        _read(path)
        for path in [ROOT / "README.md", ROOT / "docs" / "SECURITY_TEST_PLAN.md"]
        if path.exists()
    )
    assert "python scripts/run_security_tools.py" in docs
    assert "bandit" in docs
    assert "pip-audit" in docs
