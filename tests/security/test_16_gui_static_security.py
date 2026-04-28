from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GUI_ROOT = ROOT / "VetClinic" / "GUI" / "vetclinic_gui"
LOCAL_URL_RE = re.compile(r"https?://([^/\"']+)")


def _python_sources() -> list[Path]:
    assert GUI_ROOT.exists()
    return list(GUI_ROOT.rglob("*.py"))


def test_gui_does_not_use_eval_or_builtin_exec() -> None:
    findings = []
    for path in _python_sources():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if "eval(" in line or re.search(r"(^|\s)exec\(", line):
                findings.append(f"{path.relative_to(ROOT)}:{line_no}")
    assert findings == []


def test_gui_does_not_contain_hardcoded_secret_values() -> None:
    findings = []
    secret_assignment = re.compile(
        r"\b(password|token|private_key|api_key)\b\s*=\s*['\"][^'\"]+['\"]",
        re.IGNORECASE,
    )
    for path in _python_sources():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if secret_assignment.search(line):
                findings.append(f"{path.relative_to(ROOT)}:{line_no}")
            lowered = line.lower()
            if "private_key" in lowered or "api_key" in lowered:
                findings.append(f"{path.relative_to(ROOT)}:{line_no}")
    assert findings == []


def test_gui_hardcoded_urls_are_localhost_or_documented_demo_services() -> None:
    allowed_hosts = {"127.0.0.1:8000", "localhost:8000", "localhost:8001", "localhost:8002", "localhost:8003", "localhost:8004", "localhost:8005", "localhost:8006", "api.mail.gw"}
    findings = []
    for path in _python_sources():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in LOCAL_URL_RE.finditer(text):
            host = match.group(1)
            if host not in allowed_hosts:
                findings.append(f"{path.relative_to(ROOT)} -> {match.group(0)}")
    assert findings == []


def test_gui_does_not_log_authorization_headers() -> None:
    findings = []
    for path in _python_sources():
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if "authorization" in text and ("print(" in text or "logger" in text):
            findings.append(str(path.relative_to(ROOT)))
    assert findings == []
