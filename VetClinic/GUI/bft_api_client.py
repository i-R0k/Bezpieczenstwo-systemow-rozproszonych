from __future__ import annotations

from typing import Any

import requests


class BftApiClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        admin_token: str | None = None,
        timeout: float = 5.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.admin_token = admin_token
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _headers(self) -> dict[str, str]:
        if not self.admin_token:
            return {}
        return {"X-BFT-Admin-Token": self.admin_token}

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = requests.request(
                method,
                self._url(path),
                headers=self._headers(),
                timeout=self.timeout,
                **kwargs,
            )
            try:
                payload = response.json()
            except ValueError:
                payload = {"text": response.text}
            if response.status_code >= 400:
                return {
                    "ok": False,
                    "error": payload.get("detail") if isinstance(payload, dict) else str(payload),
                    "status_code": response.status_code,
                    "response": payload,
                }
            if isinstance(payload, dict):
                return {"ok": True, "status_code": response.status_code, **payload}
            return {"ok": True, "status_code": response.status_code, "data": payload}
        except requests.RequestException as exc:
            return {"ok": False, "error": str(exc), "status_code": None}

    def get_status(self) -> dict[str, Any]:
        return self._request("GET", "/bft/status")

    def get_events(self, limit: int = 50) -> dict[str, Any]:
        return self._request("GET", "/bft/events", params={"limit": limit})

    def get_communication_log(self, limit: int = 50) -> dict[str, Any]:
        return self._request("GET", "/bft/communication/log", params={"limit": limit})

    def get_swim_status(self) -> dict[str, Any]:
        return self._request("GET", "/bft/swim/status")

    def get_hotstuff_status(self) -> dict[str, Any]:
        return self._request("GET", "/bft/hotstuff/status")

    def get_narwhal_dag(self) -> dict[str, Any]:
        return self._request("GET", "/bft/narwhal/dag")

    def get_faults_status(self) -> dict[str, Any]:
        return self._request("GET", "/bft/faults/status")

    def get_checkpointing_status(self) -> dict[str, Any]:
        return self._request("GET", "/bft/checkpointing/status")

    def get_recovery_status(self) -> dict[str, Any]:
        return self._request("GET", "/bft/recovery/status")

    def get_grpc_runtime_status(self) -> dict[str, Any]:
        return self._request("GET", "/bft/grpc/runtime/status")

    def get_security_transport(self) -> dict[str, Any]:
        return self._request("GET", "/bft/security/transport")

    def run_full_demo(self) -> dict[str, Any]:
        return self._request("POST", "/bft/demo/run")

    def get_last_report(self) -> dict[str, Any]:
        return self._request("GET", "/bft/demo/last-report")

    def run_grpc_ping_demo(self) -> dict[str, Any]:
        return self._request("POST", "/bft/grpc/runtime/ping-demo")

    def create_fault_rule(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/bft/faults/rules", json=payload)

    def clear_faults(self) -> dict[str, Any]:
        return self._request("DELETE", "/bft/faults")

    def setup_totp(self, account_name: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/security/2fa/demo/setup",
            json={"account_name": account_name},
        )

    def verify_totp(
        self,
        account_name: str | None,
        secret: str | None,
        code: str,
    ) -> dict[str, Any]:
        payload = {"code": code}
        if account_name:
            payload["account_name"] = account_name
        if secret:
            payload["secret"] = secret
        return self._request("POST", "/security/2fa/demo/verify", json=payload)
