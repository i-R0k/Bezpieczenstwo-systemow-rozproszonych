from __future__ import annotations

import sys

import pytest


# Section numbers follow historical test stage/file numbers. Stages 19-24 were
# consolidated into checkpoint/recovery test_18 before crypto tests started at 25.
SECTIONS = [
    "[1] Architecture",
    "[2] Operation flow",
    "[3] Narwhal",
    "[4] HotStuff",
    "[5] SWIM",
    "[6] Full pipeline",
    "[7] Negative paths",
    "[8] Router contract",
    "[9] Full FastAPI app smoke",
    "[10] Fault injection store",
    "[11] Fault injection service",
    "[12] Replay guard",
    "[13] Equivocation detector",
    "[14] Narwhal faults integration",
    "[15] HotStuff faults integration",
    "[16] SWIM faults integration",
    "[17] Fault injection router contract",
    "[18] Checkpointing and recovery",
    "[25] Crypto keys",
    "[26] Crypto envelope",
    "[27] Crypto service",
    "[28] Crypto Narwhal integration",
    "[29] Crypto HotStuff integration",
    "[30] Crypto SWIM integration",
    "[31] Crypto checkpoint/recovery integration",
    "[32] Crypto router contract",
    "[33] Observability metrics",
    "[34] Observability health",
    "[35] Demo scenario runner",
    "[36] Observability router contract",
    "[37] Metrics duplicate registration",
    "[98] Final delivery contract",
    "[99] Documentation contract",
    "[101] gRPC contract",
    "[102] Dashboard and communication contract",
    "[103] Schedule full compliance contract",
    "[104] gRPC runtime demo",
]


def main() -> int:
    print("BFT regression testbed")
    print("Scope: local pytest testbed, no Docker, no uvicorn")
    for section in SECTIONS:
        print(section)
    return pytest.main(["tests/bft", "-q"])


if __name__ == "__main__":
    sys.exit(main())
