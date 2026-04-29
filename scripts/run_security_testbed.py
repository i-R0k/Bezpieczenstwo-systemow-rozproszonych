from __future__ import annotations

import sys

import pytest


SECTIONS = [
    "[1] Security smoke",
    "[2] API auth/authz",
    "[3] API input validation",
    "[4] VetClinic business logic",
    "[5] BFT protocol security",
    "[6] Blockchain/RPC security",
    "[7] Admin/fault abuse",
    "[8] Crypto/replay/equivocation",
    "[9] Checkpoint/recovery security",
    "[10] Secrets/config legacy scope",
    "[11] Containers/monitoring/GUI legacy scope",
    "[12] SAST/SCA wrappers legacy scope",
    "[13] Secrets/config",
    "[14] Container config",
    "[15] Monitoring exposure",
    "[16] GUI static security",
    "[17] SAST/SCA wrappers",
    "[18] mTLS contract",
    "[19] TOTP/2FA contract",
    "[20] Dashboard exposure security",
]


def main() -> int:
    print("Security regression testbed")
    print("Scope: local pytest tests, no Docker, no uvicorn")
    for section in SECTIONS:
        print(section)
    return pytest.main(["tests/security", "-q"])


if __name__ == "__main__":
    sys.exit(main())
