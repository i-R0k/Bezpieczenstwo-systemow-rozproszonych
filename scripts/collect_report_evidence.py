#!/usr/bin/env python3
"""
Collects evidence for the BSR/VetClinic report placeholders.

Run from the repository root. The script assumes that the Docker cluster/API is
already running, usually with node1 exposed at http://127.0.0.1:8001.

Examples:
  python scripts/collect_report_evidence.py --base-url http://127.0.0.1:8001
  python scripts/collect_report_evidence.py --all --base-url http://127.0.0.1:8001
  python scripts/collect_report_evidence.py --run-tests --test-cmd "python -m pytest --cov=VetClinic/API/vetclinic_api --cov=VetClinic/GUI --cov-report=term"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


Json = dict[str, Any]


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_outdir(path: str | None) -> Path:
    outdir = Path(path) if path else Path("reports") / "sprawozdanie" / now_stamp()
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir


def request_json(
    method: str,
    url: str,
    *,
    body: Json | None = None,
    admin_token: str | None = None,
    timeout: int = 20,
) -> Json:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if admin_token:
        headers["X-BFT-Admin-Token"] = admin_token

    req = Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            if not raw.strip():
                return {"ok": True, "status_code": response.status, "body": None}
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {"raw": raw}
            if isinstance(parsed, dict):
                parsed.setdefault("_http_status", response.status)
                return parsed
            return {"value": parsed, "_http_status": response.status}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail: Any = json.loads(raw)
        except json.JSONDecodeError:
            detail = raw
        return {
            "ok": False,
            "error": "HTTPError",
            "status_code": exc.code,
            "detail": detail,
            "url": url,
        }
    except URLError as exc:
        return {"ok": False, "error": "URLError", "detail": str(exc), "url": url}
    except Exception as exc:  # noqa: BLE001 - evidence collector should not crash on one failed probe
        return {"ok": False, "error": type(exc).__name__, "detail": str(exc), "url": url}


def save_json(outdir: Path, name: str, payload: Any) -> Path:
    path = outdir / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_cmd(command: str, outdir: Path, name: str, *, timeout: int | None = None) -> Json:
    env = os.environ.copy()
    pythonpath_parts = [".", "VetClinic/API", "VetClinic/GUI"]
    current_pythonpath = env.get("PYTHONPATH")
    if current_pythonpath:
        pythonpath_parts.append(current_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)

    started = time.time()
    try:
        completed = subprocess.run(
            shlex.split(command),
            cwd=Path.cwd(),
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
        output = completed.stdout or ""
        log_path = outdir / f"{name}.log"
        log_path.write_text(output, encoding="utf-8", errors="replace")
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "command": command,
            "duration_sec": round(time.time() - started, 2),
            "log_path": str(log_path),
            "output_tail": output[-4000:],
        }
    except FileNotFoundError as exc:
        log_path = outdir / f"{name}.log"
        message = (
            f"COMMAND NOT FOUND: {command}\n"
            f"{type(exc).__name__}: {exc}\n"
            "Na Windows najczęściej oznacza to nieprawidłowo sparsowaną ścieżkę do Pythona "
            "albo brak narzędzia w PATH. Użyj --pentest-cmd/--test-cmd z cudzysłowem "
            "wokół ścieżki do interpretera albo uruchom skrypt przez `py`.\n"
        )
        log_path.write_text(message, encoding="utf-8", errors="replace")
        return {
            "ok": False,
            "returncode": None,
            "command": command,
            "duration_sec": round(time.time() - started, 2),
            "log_path": str(log_path),
            "error": "file_not_found",
            "output_tail": message[-4000:],
        }
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        log_path = outdir / f"{name}.log"
        log_path.write_text(output, encoding="utf-8", errors="replace")
        return {
            "ok": False,
            "returncode": None,
            "command": command,
            "duration_sec": round(time.time() - started, 2),
            "log_path": str(log_path),
            "error": f"timeout after {timeout}s",
            "output_tail": output[-4000:],
        }


def collect_cluster(base_url: str, outdir: Path) -> tuple[Json, dict[str, str]]:
    topology = request_json("GET", f"{base_url}/bft/cluster/topology")
    status = request_json("GET", f"{base_url}/bft/status")
    topology_path = save_json(outdir, "cluster_topology", topology)
    status_path = save_json(outdir, "bft_status", status)

    total = topology.get("configured_total_nodes") or status.get("total_nodes")
    warning = topology.get("warning")
    ok = total == 6 and not warning
    result = (
        "Klaster Docker uruchomiony poprawnie; dashboard/API połączony z Docker node1 "
        f"pod {base_url}; configured_total_nodes = {total}."
        if ok
        else (
            f"Wymaga sprawdzenia: configured_total_nodes = {total}, warning = {warning!r}. "
            f"Zweryfikuj, czy targetem jest Docker node1 ({base_url}), a nie standalone API."
        )
    )
    proof = f"{topology_path}; {status_path}"
    return {"topology": topology, "status": status, "ok": ok}, {
        "WYNIK_KLASTER": result,
        "DOWOD_KLASTER": proof,
    }


def collect_bft_demo(base_url: str, outdir: Path, admin_token: str | None) -> tuple[Json, dict[str, str]]:
    run_result = request_json("POST", f"{base_url}/bft/demo/run", admin_token=admin_token, timeout=60)
    report = request_json("GET", f"{base_url}/bft/demo/last-report", admin_token=admin_token, timeout=20)
    run_path = save_json(outdir, "bft_demo_run", run_result)
    report_path = save_json(outdir, "bft_demo_last_report", report)

    status = report.get("status") or run_result.get("status")
    final_status = report.get("final_operation_status") or run_result.get("final_operation_status")
    checkpoint_id = report.get("checkpoint_id") or run_result.get("checkpoint_id")
    recovered_node_id = report.get("recovered_node_id") or run_result.get("recovered_node_id")
    ok = status == "ok" and final_status in {"EXECUTED", "COMMITTED"} and bool(checkpoint_id)
    result = (
        "Pełny scenariusz BFT zakończony sukcesem; "
        f"status = {status}, final_operation_status = {final_status}, "
        f"checkpoint_id obecny, recovered_node_id = {recovered_node_id}."
        if ok
        else (
            "Pełny scenariusz BFT wymaga sprawdzenia; "
            f"status = {status}, final_operation_status = {final_status}, "
            f"checkpoint_id = {checkpoint_id}, recovered_node_id = {recovered_node_id}."
        )
    )
    proof = f"{run_path}; {report_path}"
    return {"run": run_result, "report": report, "ok": ok}, {
        "WYNIK_BFT_DEMO": result,
        "DOWOD_BFT_DEMO": proof,
    }


def collect_reset(
    base_url: str,
    ports: list[int],
    outdir: Path,
    admin_token: str | None,
) -> tuple[Json, dict[str, str]]:
    reset_result = request_json(
        "POST",
        f"{base_url}/admin/network/reset-demo-chain?scope=cluster",
        admin_token=admin_token,
        timeout=60,
    )
    reset_path = save_json(outdir, "cluster_reset", reset_result)

    per_node: dict[str, Any] = {}
    for port in ports:
        node_url = f"http://127.0.0.1:{port}"
        status = request_json("GET", f"{node_url}/chain/status", timeout=20)
        verify = request_json("GET", f"{node_url}/chain/verify", timeout=20)
        per_node[str(port)] = {"status": status, "verify": verify}
    per_node_path = save_json(outdir, "reset_per_node_status_verify", per_node)

    def node_is_clean(item: Json) -> bool:
        status = item.get("status", {})
        verify = item.get("verify", {})
        height = status.get("height", verify.get("height"))
        verification_status = verify.get("verification_status")
        valid = verify.get("valid")
        return height == 0 and (verification_status == "VALID" or valid is True)

    clean_nodes = [port for port, payload in per_node.items() if node_is_clean(payload)]
    ok = len(clean_nodes) == len(ports)
    result = (
        f"Reset scope=cluster wykonany poprawnie; {len(clean_nodes)}/{len(ports)} node'ów ma "
        "height = 0 i verification_status = VALID."
        if ok
        else (
            f"Reset scope=cluster wymaga sprawdzenia; {len(clean_nodes)}/{len(ports)} node'ów ma "
            "height = 0 i VALID. Sprawdź szczegóły per node."
        )
    )
    proof = f"{reset_path}; {per_node_path}"
    return {"reset": reset_result, "per_node": per_node, "ok": ok}, {
        "WYNIK_RESET": result,
        "DOWOD_RESET": proof,
    }


def collect_fault_injection(base_url: str, outdir: Path, admin_token: str | None) -> tuple[Json, dict[str, str]]:
    # Clean stale rules first to avoid misinterpreting an old demo state.
    clear_before = request_json("DELETE", f"{base_url}/bft/faults", admin_token=admin_token, timeout=20)
    rule_payload = {
        "fault_type": "DROP",
        "protocol": "HOTSTUFF",
        "message_kind": "VOTE",
        "source_node_id": 2,
        "target_node_id": 1,
        "probability": 1.0,
        "metadata": {"report_evidence": True},
    }
    created_rule = request_json(
        "POST",
        f"{base_url}/bft/faults/rules",
        body=rule_payload,
        admin_token=admin_token,
        timeout=20,
    )
    status_with_rule = request_json("GET", f"{base_url}/bft/faults/status", timeout=20)
    clear_after = request_json("DELETE", f"{base_url}/bft/faults", admin_token=admin_token, timeout=20)

    payload = {
        "clear_before": clear_before,
        "created_rule": created_rule,
        "status_with_rule": status_with_rule,
        "clear_after": clear_after,
    }
    proof_path = save_json(outdir, "fault_injection_probe", payload)

    rules = status_with_rule.get("rules") or []
    rules_count = status_with_rule.get("rules_count")
    ok = bool(created_rule.get("rule_id") or rules or (isinstance(rules_count, int) and rules_count > 0))
    result = (
        "Fault injection działa; dodano regułę DROP dla HOTSTUFF/VOTE, system zaraportował "
        "aktywną regułę i po teście stan faultów został wyczyszczony."
        if ok
        else "Fault injection wymaga sprawdzenia; reguła testowa nie została jednoznacznie zaraportowana."
    )
    proof = str(proof_path)
    return {"payload": payload, "ok": ok}, {
        "WYNIK_FAULT_INJECTION": result,
        "DOWOD_FAULT_INJECTION": proof,
    }


def newest_pentest_report_dir() -> str | None:
    root_candidates = [Path("reports/pentest"), Path("pentest/reports")]
    dirs: list[Path] = []
    for root in root_candidates:
        if root.exists():
            dirs.extend([p for p in root.iterdir() if p.is_dir()])
    if not dirs:
        return None
    newest = max(dirs, key=lambda p: p.stat().st_mtime)
    return str(newest)


def collect_pentest(outdir: Path, command: str, timeout: int) -> tuple[Json, dict[str, str]]:
    result = run_cmd(command, outdir, "pentest_quick", timeout=timeout)
    report_dir = newest_pentest_report_dir()
    if report_dir:
        result["detected_report_dir"] = report_dir
    save_json(outdir, "pentest_result", result)

    text = (
        "Pentest quick zakończony bez błędu wykonania; harness wykonał lokalne probe HTTP "
        f"i zapisał raport w {report_dir or 'reports/pentest/<timestamp>/'} ."
        if result["ok"]
        else (
            "Pentest quick wymaga sprawdzenia; komenda zakończyła się błędem. "
            f"Szczegóły w logu: {result['log_path']}"
        )
    )
    proof = result["log_path"] if not report_dir else f"{result['log_path']}; {report_dir}"
    return result, {"WYNIK_PENTEST": text, "DOWOD_PENTEST": proof}


def parse_pytest_output(output: str) -> tuple[int | None, str | None]:
    # Handles forms such as "529 passed" and coverage rows like "TOTAL ... 84%".
    passed_match = re.search(r"(?P<passed>\d+)\s+passed", output)
    passed = int(passed_match.group("passed")) if passed_match else None

    coverage_match = re.search(r"^TOTAL\s+.*?\s+(?P<coverage>\d+(?:\.\d+)?)%", output, re.MULTILINE)
    coverage = f"{coverage_match.group('coverage')}%" if coverage_match else None
    return passed, coverage


def collect_tests(outdir: Path, command: str, timeout: int) -> tuple[Json, dict[str, str]]:
    result = run_cmd(command, outdir, "pytest_coverage", timeout=timeout)
    output = result.get("output_tail", "")
    # If the interesting part was earlier than the tail, parse the full log too.
    try:
        output = Path(result["log_path"]).read_text(encoding="utf-8", errors="replace")
    except Exception:
        pass
    passed, coverage = parse_pytest_output(output)
    result["parsed_passed"] = passed
    result["parsed_coverage"] = coverage
    save_json(outdir, "tests_result", result)

    if result["ok"] and passed and coverage:
        text = f"{passed} testów jednostkowych zakończonych sukcesem; coverage total = {coverage}."
    elif result["ok"]:
        text = "Testy zakończone sukcesem, ale parser nie odczytał liczby testów lub coverage; sprawdź log pytest."
    else:
        text = "Testy wymagają sprawdzenia; komenda zakończyła się błędem."
    proof = result["log_path"]
    return result, {"WYNIK_TESTOW": text, "DOWOD_TESTOW": proof}


def write_markdown_table(outdir: Path, replacements: dict[str, str]) -> Path:
    rows = [
        ("Uruchomienie klastra", "WYNIK_KLASTER", "DOWOD_KLASTER"),
        ("Pełny BFT demo", "WYNIK_BFT_DEMO", "DOWOD_BFT_DEMO"),
        ("Reset demo chain", "WYNIK_RESET", "DOWOD_RESET"),
        ("Fault injection", "WYNIK_FAULT_INJECTION", "DOWOD_FAULT_INJECTION"),
        ("Testy penetracyjne", "WYNIK_PENTEST", "DOWOD_PENTEST"),
        ("Testy automatyczne", "WYNIK_TESTOW", "DOWOD_TESTOW"),
    ]
    lines = ["| Scenariusz | Uzyskany wynik | Dowód |", "|---|---|---|"]
    for label, result_key, proof_key in rows:
        lines.append(
            f"| {label} | {replacements.get(result_key, 'Pominięto w tym uruchomieniu.')} "
            f"| {replacements.get(proof_key, 'Brak wygenerowanego dowodu.')} |"
        )
    path = outdir / "wyniki_do_wklejenia.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def parse_ports(raw: str) -> list[int]:
    ports: list[int] = []
    for item in raw.split(","):
        item = item.strip()
        if item:
            ports.append(int(item))
    return ports


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect evidence for BSR report placeholders.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--ports", default="8001,8002,8003,8004,8005,8006")
    parser.add_argument("--outdir", default=None)
    parser.add_argument("--admin-token", default=os.getenv("BFT_ADMIN_TOKEN"))
    parser.add_argument("--all", action="store_true", help="Run demo, reset, fault, pentest and tests collectors.")
    parser.add_argument("--run-demo", action="store_true")
    parser.add_argument("--run-reset", action="store_true")
    parser.add_argument("--run-fault", action="store_true")
    parser.add_argument("--run-pentest", action="store_true")
    parser.add_argument("--run-tests", action="store_true")
    parser.add_argument(
        "--pentest-cmd",
        default=subprocess.list2cmdline([sys.executable, "scripts/run_pentest_local.py", "--quick"]),
    )
    parser.add_argument(
        "--test-cmd",
        default=subprocess.list2cmdline([
            sys.executable,
            "-m",
            "pytest",
            "--cov=VetClinic/API/vetclinic_api",
            "--cov=VetClinic/GUI",
            "--cov-report=term",
        ]),
    )
    parser.add_argument("--pentest-timeout", type=int, default=300)
    parser.add_argument("--tests-timeout", type=int, default=900)
    args = parser.parse_args()

    if args.all:
        args.run_demo = args.run_reset = args.run_fault = args.run_pentest = args.run_tests = True

    outdir = ensure_outdir(args.outdir)
    ports = parse_ports(args.ports)
    replacements: dict[str, str] = {}
    evidence: dict[str, Any] = {"outdir": str(outdir), "base_url": args.base_url, "ports": ports}

    cluster, cluster_repl = collect_cluster(args.base_url, outdir)
    evidence["cluster"] = cluster
    replacements.update(cluster_repl)

    if args.run_demo:
        demo, demo_repl = collect_bft_demo(args.base_url, outdir, args.admin_token)
        evidence["bft_demo"] = demo
        replacements.update(demo_repl)

    if args.run_reset:
        reset, reset_repl = collect_reset(args.base_url, ports, outdir, args.admin_token)
        evidence["reset"] = reset
        replacements.update(reset_repl)

    if args.run_fault:
        fault, fault_repl = collect_fault_injection(args.base_url, outdir, args.admin_token)
        evidence["fault_injection"] = fault
        replacements.update(fault_repl)

    if args.run_pentest:
        pentest, pentest_repl = collect_pentest(outdir, args.pentest_cmd, args.pentest_timeout)
        evidence["pentest"] = pentest
        replacements.update(pentest_repl)

    if args.run_tests:
        tests, tests_repl = collect_tests(outdir, args.test_cmd, args.tests_timeout)
        evidence["tests"] = tests
        replacements.update(tests_repl)

    replacements_path = save_json(outdir, "replacements", replacements)
    evidence_path = save_json(outdir, "evidence", evidence)
    table_path = write_markdown_table(outdir, replacements)

    print(f"\nZapisano dowody w: {outdir}")
    print(f"- replacements: {replacements_path}")
    print(f"- evidence:      {evidence_path}")
    print(f"- tabela MD:     {table_path}")
    print("\nWartości do wklejenia:")
    print(json.dumps(replacements, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
