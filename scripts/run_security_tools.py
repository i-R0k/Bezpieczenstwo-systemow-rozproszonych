from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "security"
SUMMARY = REPORT_DIR / "security-summary.md"


def run_tool(name: str, command: list[str], blocking: bool = True) -> tuple[str, int, bool]:
    executable = command[0]
    if executable not in {"python", sys.executable} and shutil.which(executable) is None:
        return name, 127, blocking

    print(f"[security-tools] {name}: {' '.join(command)}")
    completed = subprocess.run(command, cwd=ROOT)
    return name, completed.returncode, blocking


def write_summary(results: list[tuple[str, int, bool]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Security tools summary",
        "",
        "| Tool | Exit code | Blocking |",
        "|---|---:|---|",
    ]
    for name, code, blocking in results:
        lines.append(f"| {name} | {code} | {'yes' if blocking else 'no'} |")
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[security-tools] summary written to {SUMMARY}")


def main() -> int:
    results: list[tuple[str, int, bool]] = []
    results.append(
        run_tool(
            "pytest-security",
            [sys.executable, "-m", "pytest", "tests/security", "-q"],
            blocking=True,
        )
    )
    results.append(
        run_tool(
            "bandit",
            ["bandit", "-r", "VetClinic/API/vetclinic_api", "-x", "tests"],
            blocking=True,
        )
    )
    results.append(
        run_tool(
            "pip-audit",
            ["pip-audit", "-r", "requirements-api.txt"],
            blocking=True,
        )
    )

    if shutil.which("semgrep"):
        results.append(
            run_tool(
                "semgrep",
                ["semgrep", "scan", "--config", "p/python", "VetClinic/API/vetclinic_api"],
                blocking=False,
            )
        )
    else:
        results.append(("semgrep", 127, False))

    if shutil.which("trivy"):
        results.append(
            run_tool(
                "trivy",
                ["trivy", "fs", "--scanners", "vuln,secret,misconfig", "."],
                blocking=False,
            )
        )
    else:
        results.append(("trivy", 127, False))

    write_summary(results)
    blocking_failures = [code for _, code, blocking in results if blocking and code not in (0, 127)]
    return 1 if blocking_failures else 0


if __name__ == "__main__":
    sys.exit(main())
