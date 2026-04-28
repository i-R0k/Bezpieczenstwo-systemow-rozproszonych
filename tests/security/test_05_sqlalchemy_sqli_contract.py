from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "VetClinic" / "API" / "vetclinic_api"
SQLI_PAYLOAD = "' OR 1=1 --"


def test_sql_injection_payloads_on_common_api_fields_do_not_return_500(security_full_app_client):
    requests = [
        security_full_app_client.get(f"/users/?search={SQLI_PAYLOAD}"),
        security_full_app_client.get(f"/doctors/?name={SQLI_PAYLOAD}"),
        security_full_app_client.get(f"/animals/?name={SQLI_PAYLOAD}"),
        security_full_app_client.post(
            "/users/login",
            json={"email": f"attacker{SQLI_PAYLOAD}@example.com", "password": SQLI_PAYLOAD},
        ),
        security_full_app_client.post(
            "/tx/submit",
            json={"sender": SQLI_PAYLOAD, "recipient": "bob", "amount": 1},
        ),
    ]

    for response in requests:
        assert response.status_code != 500


def test_search_like_payload_does_not_bypass_into_unbounded_dump(security_full_app_client):
    baseline = security_full_app_client.get("/users/")
    injected = security_full_app_client.get(f"/users/?search={SQLI_PAYLOAD}")

    assert injected.status_code != 500
    if baseline.status_code == 200 and injected.status_code == 200:
        assert len(injected.json()) <= len(baseline.json())


def test_static_sql_construction_does_not_use_f_string_execute_or_text():
    forbidden_patterns = [
        '.execute(f"',
        ".execute(f'",
        'text(f"',
        "text(f'",
    ]
    offenders: list[str] = []

    for path in API_ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in forbidden_patterns:
            if pattern in text:
                offenders.append(f"{rel}: {pattern}")
        lowered = text.lower()
        if "raw sql" in lowered and "allowlist: raw sql reviewed" not in lowered:
            offenders.append(f"{rel}: raw SQL")

    assert offenders == []

