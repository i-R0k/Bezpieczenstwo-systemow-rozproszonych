from __future__ import annotations

from fastapi.testclient import TestClient

import vetclinic_api.admin.network_router as network_router
from vetclinic_api.blockchain.core import InMemoryStorage
from vetclinic_api.blockchain.deps import get_storage
from vetclinic_api.cluster.http_client import get_http_client
from vetclinic_api.main import app


class FakeAsyncClient:
    def __init__(self, responses=None):
        self.calls: list[dict] = []
        self.responses = responses or {}

    async def post(self, url: str, **kwargs):
        self.calls.append({"url": url, **kwargs})
        result = self.responses.get(url)
        if isinstance(result, Exception):
            raise result
        return result or FakeResponse(200, {"ok": True, "height": 0, "verification_status": "VALID"})


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.content = b"{}"
        self.text = str(payload)

    def json(self):
        return self._payload


def _setup(monkeypatch, fake_client: FakeAsyncClient):
    storage = InMemoryStorage()
    monkeypatch.setattr(
        network_router.CONFIG,
        "peers",
        ["http://node2:8000", "http://node3:8000"],
    )
    monkeypatch.setattr(network_router.CONFIG, "node_id", 1)
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_http_client] = lambda: fake_client
    return storage


def test_cluster_reset_calls_each_peer_with_local_scope(monkeypatch) -> None:
    fake_client = FakeAsyncClient()
    _setup(monkeypatch, fake_client)

    with TestClient(app) as client:
        response = client.post("/admin/network/reset-demo-chain?scope=cluster")

    assert response.status_code == 200
    assert [call["params"] for call in fake_client.calls] == [
        {"scope": "local"},
        {"scope": "local"},
    ]
    assert {item["node"] for item in response.json()["results"]} == {
        "node1",
        "node2",
        "node3",
    }


def test_cluster_reset_reports_partial_peer_failure(monkeypatch) -> None:
    fake_client = FakeAsyncClient(
        {
            "http://node3:8000/admin/network/reset-demo-chain": RuntimeError("boom"),
        }
    )
    _setup(monkeypatch, fake_client)

    with TestClient(app) as client:
        response = client.post("/admin/network/reset-demo-chain?scope=cluster")

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "partial_failure"
    assert any(item["node"] == "node3" and item["ok"] is False for item in body["results"])


def test_cluster_reset_forwards_admin_token_in_strict_mode(monkeypatch) -> None:
    fake_client = FakeAsyncClient()
    _setup(monkeypatch, fake_client)
    monkeypatch.setenv("BFT_SECURITY_MODE", "strict")
    monkeypatch.setenv("BFT_ADMIN_TOKEN", "secret")

    with TestClient(app) as client:
        response = client.post(
            "/admin/network/reset-demo-chain?scope=cluster",
            headers={"X-BFT-Admin-Token": "secret"},
        )

    assert response.status_code == 200
    assert fake_client.calls
    assert all(
        call["headers"] == {"X-BFT-Admin-Token": "secret"}
        for call in fake_client.calls
    )
