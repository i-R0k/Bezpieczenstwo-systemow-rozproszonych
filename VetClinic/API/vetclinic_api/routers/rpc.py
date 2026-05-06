from __future__ import annotations

from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException

from vetclinic_api.admin.network_state import get_state
from vetclinic_api.cluster.config import CONFIG
from vetclinic_api.cluster.http_client import get_http_client
from vetclinic_api.blockchain.core import (
    BlockProposal,
    Storage,
    compute_block_hash,
    validate_block_for_append,
)
from vetclinic_api.blockchain.deps import get_storage
from vetclinic_api.middleware.chaos import apply_rpc_faults

router = APIRouter(prefix="/rpc", tags=["rpc"])


@router.get("/node-info")
async def node_info():
    """
    Zwraca podstawowe informacje o tym węźle.
    """
    await apply_rpc_faults("node_info")
    return {
        "node_id": CONFIG.node_id,
        "leader_id": CONFIG.leader_id,
        "peers": CONFIG.peers,
    }


@router.get("/leader-info")
async def leader_info():
    """
    Zwraca identyfikator lidera znany temu węźle.
    """
    await apply_rpc_faults("leader_info")
    return {"leader_id": CONFIG.leader_id}


@router.get("/ping-peers")
async def ping_peers(
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Testowo odpytuje wszystkich peers o /rpc/node-info.
    Nie jest to mechanizm konsensusu, tylko diagnostyka sieci.
    """
    await apply_rpc_faults("ping_peers")
    results: List[dict] = []
    for base_url in CONFIG.peers:
        url = f"{base_url.rstrip('/')}/rpc/node-info"
        try:
            resp = await client.get(url)
            ok = resp.status_code == 200
            payload = resp.json() if ok else None
            results.append(
                {
                    "url": url,
                    "ok": ok,
                    "response": payload,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "url": url,
                    "ok": False,
                    "error": str(exc),
                }
            )
    return {
        "node_id": CONFIG.node_id,
        "leader_id": CONFIG.leader_id,
        "results": results,
    }


@router.post("/propose_block")
async def propose_block(
    proposal: BlockProposal,
    storage: Storage = Depends(get_storage),
):
    """
    Waliduje i głosuje nad propozycją bloku.
    """
    await apply_rpc_faults("propose_block")

    chain = storage.get_chain()
    if not chain:
        raise HTTPException(status_code=500, detail="Empty chain on follower")

    last = chain[-1]

    is_ok = True
    reason = None
    computed_hash = compute_block_hash(proposal.block)
    try:
        validate_block_for_append(last, proposal.block)
        if computed_hash != proposal.hash:
            is_ok = False
            reason = "proposal hash mismatch"
    except ValueError as exc:
        is_ok = False
        reason = str(exc)

    state = get_state()
    vote = "accept" if is_ok else "reject"
    if state.byzantine:
        vote = "reject" if is_ok else "accept"

    return {
        "vote": vote,
        "byzantine": state.byzantine,
        "reason": reason,
        "height": last.index,
        "expected_previous_hash": compute_block_hash(last),
        "proposal_previous_hash": proposal.block.previous_hash,
    }


@router.post("/commit_block")
async def commit_block(
    proposal: BlockProposal,
    storage: Storage = Depends(get_storage),
):
    """
    Przyjmuje zatwierdzony blok i dodaje do łańcucha.
    """
    await apply_rpc_faults("commit_block")

    chain = storage.get_chain()
    if not chain:
        raise HTTPException(status_code=500, detail="Empty chain on commit")

    last = chain[-1]
    try:
        validate_block_for_append(last, proposal.block)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    state = get_state()
    if state.byzantine:
        return {"status": "committed", "byzantine": True, "height": last.index}

    try:
        storage.add_block(proposal.block)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "status": "committed",
        "byzantine": False,
        "height": proposal.block.index,
    }
