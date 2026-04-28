from __future__ import annotations


def _validate_node_count(n: int) -> None:
    if n <= 0:
        raise ValueError("n must be greater than 0")


def fault_tolerance(n: int) -> int:
    _validate_node_count(n)
    return (n - 1) // 3


def quorum_size(n: int) -> int:
    f = fault_tolerance(n)
    return 2 * f + 1


def has_quorum(votes: int, n: int) -> bool:
    _validate_node_count(n)
    if votes < 0:
        raise ValueError("votes must be greater than or equal to 0")
    return votes >= quorum_size(n)


def describe_quorum(n: int) -> dict:
    f = fault_tolerance(n)
    quorum = 2 * f + 1
    return {
        "nodes": n,
        "fault_tolerance": f,
        "quorum": quorum,
        "rule": "2f + 1",
    }
