from __future__ import annotations

import os

from fastapi import HTTPException, Request


ADMIN_TOKEN_HEADER = "X-BFT-Admin-Token"


def get_security_mode() -> str:
    return os.getenv("BFT_SECURITY_MODE", "demo").strip().lower() or "demo"


def get_admin_token() -> str | None:
    token = os.getenv("BFT_ADMIN_TOKEN")
    return token if token else None


def is_strict_mode() -> bool:
    return get_security_mode() == "strict"


def get_max_list_limit() -> int:
    return int(os.getenv("BFT_MAX_LIST_LIMIT", "1000"))


def get_max_batch_operations() -> int:
    return int(os.getenv("BFT_MAX_BATCH_OPERATIONS", "100"))


def get_max_payload_bytes() -> int:
    return int(os.getenv("BFT_MAX_PAYLOAD_BYTES", "65536"))


def require_admin_token(request: Request) -> None:
    if not is_strict_mode():
        return

    expected = get_admin_token()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="BFT strict security mode is enabled but BFT_ADMIN_TOKEN is not configured",
        )

    provided = request.headers.get(ADMIN_TOKEN_HEADER)
    if not provided:
        raise HTTPException(status_code=401, detail=f"Missing required {ADMIN_TOKEN_HEADER} header")
    if provided != expected:
        raise HTTPException(status_code=403, detail="Invalid BFT admin token")
