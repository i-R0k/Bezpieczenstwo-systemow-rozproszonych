from __future__ import annotations

import sys
from pathlib import Path

import pytest

API_PATH = Path(__file__).resolve().parents[1] / "VetClinic" / "API"
if str(API_PATH) not in sys.path:
    sys.path.insert(0, str(API_PATH))

from vetclinic_api.bft.common.quorum import (  # noqa: E402
    describe_quorum,
    fault_tolerance,
    has_quorum,
    quorum_size,
)


@pytest.mark.parametrize(
    ("n", "expected_f", "expected_quorum"),
    [
        (1, 0, 1),
        (4, 1, 3),
        (6, 1, 3),
        (7, 2, 5),
    ],
)
def test_bft_quorum_values(n: int, expected_f: int, expected_quorum: int) -> None:
    assert fault_tolerance(n) == expected_f
    assert quorum_size(n) == expected_quorum

    description = describe_quorum(n)
    assert description["nodes"] == n
    assert description["fault_tolerance"] == expected_f
    assert description["quorum"] == expected_quorum
    assert description["rule"] == "2f + 1"


def test_has_quorum_uses_bft_threshold_not_plain_majority() -> None:
    assert has_quorum(3, 6) is True
    assert has_quorum(2, 6) is False
    assert has_quorum(5, 7) is True
    assert has_quorum(4, 7) is False


@pytest.mark.parametrize("n", [0, -1])
def test_invalid_node_count_is_rejected(n: int) -> None:
    with pytest.raises(ValueError):
        fault_tolerance(n)
    with pytest.raises(ValueError):
        quorum_size(n)
    with pytest.raises(ValueError):
        describe_quorum(n)
    with pytest.raises(ValueError):
        has_quorum(1, n)


def test_invalid_vote_count_is_rejected() -> None:
    with pytest.raises(ValueError):
        has_quorum(-1, 4)
