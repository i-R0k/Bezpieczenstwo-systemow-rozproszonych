from __future__ import annotations

from typing import Any, Dict

import httpx
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from vetclinic_api.admin.network_state import get_state, state_payload, update_state
from vetclinic_api.blockchain.core import Storage, compute_block_hash, verify_chain
from vetclinic_api.blockchain.deps import get_storage
from vetclinic_api.cluster.config import CONFIG
from vetclinic_api.cluster.http_client import get_http_client
from vetclinic_api.security_mode import ADMIN_TOKEN_HEADER, require_admin_token

ADMIN_DEPENDENCIES = [Depends(require_admin_token)]

router = APIRouter(prefix="/admin/network", tags=["admin-network"])

SIM_FIELDS = [
    "traffic_enabled",
    "traffic_rps",
    "chaos_enabled",
    "chaos_error_rate",
    "chaos_delay_rate",
    "chaos_delay_ms_min",
    "chaos_delay_ms_max",
]

FAULT_FIELDS = [
    "offline",
    "slow_ms",
    "byzantine",
    "flapping",
    "flapping_mod",
    "drop_rpc_prob",
    "drop_rpc_probability",
]


def _select_payload(fields: list[str]) -> Dict[str, Any]:
    data = state_payload()
    return {field: data[field] for field in fields}


class NetworkSimPayload(BaseModel):
    traffic_enabled: bool
    traffic_rps: float
    chaos_enabled: bool
    chaos_error_rate: float
    chaos_delay_rate: float
    chaos_delay_ms_min: int
    chaos_delay_ms_max: int


class NetworkSimUpdate(BaseModel):
    traffic_enabled: bool | None = None
    traffic_rps: float | None = None
    chaos_enabled: bool | None = None
    chaos_error_rate: float | None = None
    chaos_delay_rate: float | None = None
    chaos_delay_ms_min: int | None = None
    chaos_delay_ms_max: int | None = None


class RpcFaultsPayload(BaseModel):
    offline: bool
    slow_ms: int
    byzantine: bool
    flapping: bool
    flapping_mod: int
    drop_rpc_prob: float
    drop_rpc_probability: float


class RpcFaultsUpdate(BaseModel):
    offline: bool | None = None
    slow_ms: int | None = Field(default=None, ge=0)
    byzantine: bool | None = None
    flapping: bool | None = None
    flapping_mod: int | None = Field(default=None, ge=0)
    drop_rpc_prob: float | None = Field(default=None, ge=0.0, le=1.0)
    drop_rpc_probability: float | None = Field(default=None, ge=0.0, le=1.0)


@router.get("/sim", response_model=NetworkSimPayload)
def get_sim_state():
    return NetworkSimPayload(**_select_payload(SIM_FIELDS))


@router.put("/sim", response_model=NetworkSimPayload, dependencies=ADMIN_DEPENDENCIES)
def set_sim_state(payload: NetworkSimUpdate):
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        update_state(**updates)
    return NetworkSimPayload(**_select_payload(SIM_FIELDS))


@router.get("/state", response_model=RpcFaultsPayload)
def get_fault_state():
    return RpcFaultsPayload(**_select_payload(FAULT_FIELDS))


@router.put("/state", response_model=RpcFaultsPayload, dependencies=ADMIN_DEPENDENCIES)
def set_fault_state(payload: RpcFaultsUpdate):
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        update_state(**updates)
    return RpcFaultsPayload(**_select_payload(FAULT_FIELDS))


def _node_name_for_url(url: str) -> str:
    for node_id in range(1, 100):
        if f"node{node_id}" in url:
            return f"node{node_id}"
    return url


def _local_reset_result(storage: Storage, node: str, url: str) -> dict:
    genesis = storage.reset_demo_chain()
    get_state().reset_counters()
    verification = verify_chain(storage)
    return {
        "node": node,
        "url": url,
        "ok": verification.get("verification_status") == "VALID",
        "status": "ok",
        "height": 0,
        "last_hash": compute_block_hash(genesis),
        "verification_status": verification.get("verification_status", "VALID"),
        "valid": verification.get("valid"),
        **({"error": verification.get("reason")} if verification.get("verification_status") != "VALID" else {}),
    }


@router.post("/reset-demo-chain", dependencies=ADMIN_DEPENDENCIES)
async def reset_demo_chain(
    request: Request,
    scope: str = Query(default="local", pattern="^(local|cluster)$"),
    storage: Storage = Depends(get_storage),
    client: httpx.AsyncClient = Depends(get_http_client),
) -> dict:
    if scope == "local":
        local = _local_reset_result(
            storage,
            node=f"node{CONFIG.node_id}",
            url=f"http://node{CONFIG.node_id}:8000",
        )
        return {
            **local,
            "scope": "local",
            "message": "local demo chain reset to deterministic genesis",
            "results": [local],
        }

    previous_traffic_enabled = state_payload().get("traffic_enabled")
    update_state(traffic_enabled=False)

    local = _local_reset_result(
        storage,
        node=f"node{CONFIG.node_id}",
        url=f"http://node{CONFIG.node_id}:8000",
    )
    results: list[dict] = [local]

    headers: dict[str, str] = {}
    admin_token = request.headers.get(ADMIN_TOKEN_HEADER)
    if admin_token:
        headers[ADMIN_TOKEN_HEADER] = admin_token

    for base_url in CONFIG.peers:
        node = _node_name_for_url(base_url)
        endpoint = f"{base_url.rstrip('/')}/admin/network/reset-demo-chain"
        try:
            response = await client.post(
                endpoint,
                params={"scope": "local"},
                headers=headers,
            )
            try:
                payload = response.json()
            except ValueError:
                payload = {"detail": response.text}
            if response.status_code >= 400:
                results.append(
                    {
                        "node": node,
                        "url": base_url,
                        "ok": False,
                        "height": None,
                        "verification_status": "ERROR",
                        "error": payload.get("detail", response.text),
                    }
                )
                continue
            results.append(
                {
                    "node": payload.get("node", node),
                    "url": base_url,
                    "ok": bool(payload.get("ok", True)),
                    "height": payload.get("height"),
                    "verification_status": payload.get("verification_status", "UNKNOWN"),
                    **({"error": payload.get("error")} if payload.get("error") else {}),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "node": node,
                    "url": base_url,
                    "ok": False,
                    "height": None,
                    "verification_status": "ERROR",
                    "error": str(exc),
                }
            )

    all_ok = all(item.get("ok") for item in results)
    return {
        "status": "ok" if all_ok else "partial_failure",
        "scope": "cluster",
        "traffic_enabled_before_reset": previous_traffic_enabled,
        "traffic_enabled_after_reset": state_payload().get("traffic_enabled"),
        "message": (
            "cluster demo chain reset issued; traffic_enabled was disabled on this node. "
            "Stop trafficgen or keep traffic disabled during diagnostics."
        ),
        "results": results,
        "configured_total_nodes": 1 + len(CONFIG.peers),
        "ok": all_ok,
        "height": local["height"],
        "last_hash": local["last_hash"],
        "verification_status": local["verification_status"],
        "valid": local["valid"],
    }
