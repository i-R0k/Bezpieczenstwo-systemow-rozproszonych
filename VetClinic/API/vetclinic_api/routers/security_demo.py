from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from vetclinic_api.security.totp import verify_totp_code
from vetclinic_api.security.totp_store import TOTP_DEMO_STORE
from vetclinic_api.security_mode import require_admin_token


router = APIRouter(prefix="/security/2fa/demo", tags=["security-demo"])
ADMIN_DEPENDENCIES = [Depends(require_admin_token)]
ISSUER = "BSR-BFT-Demo"


class TotpSetupRequest(BaseModel):
    account_name: str = Field(min_length=1)


class TotpSetupResponse(BaseModel):
    account_name: str
    secret: str
    provisioning_uri: str
    issuer: str
    demo_warning: str


class TotpVerifyRequest(BaseModel):
    account_name: str | None = Field(default=None, min_length=1)
    secret: str | None = Field(default=None, min_length=1)
    code: str = Field(min_length=1)


@router.post("/setup", response_model=TotpSetupResponse)
def setup_totp_demo(request: TotpSetupRequest) -> TotpSetupResponse:
    payload = TOTP_DEMO_STORE.create_secret(request.account_name)
    return TotpSetupResponse(
        account_name=payload["account_name"],
        secret=payload["secret"],
        provisioning_uri=payload["provisioning_uri"],
        issuer=ISSUER,
        demo_warning="Demo-only in-memory TOTP secret. Do not use as production enrollment.",
    )


@router.post("/verify")
def verify_totp_demo(request: TotpVerifyRequest) -> dict:
    if request.secret:
        secret = request.secret
    elif request.account_name:
        try:
            secret = TOTP_DEMO_STORE.get_secret(request.account_name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    else:
        raise HTTPException(status_code=400, detail="Provide either secret or account_name")

    return {
        "valid": verify_totp_code(secret, request.code),
        "account_name": request.account_name,
        "issuer": ISSUER,
    }


@router.delete("", dependencies=ADMIN_DEPENDENCIES)
def clear_totp_demo_store() -> dict:
    TOTP_DEMO_STORE.clear()
    return {"status": "cleared"}
