from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from vetclinic_api.bft.common.types import OperationStatus, ProtocolName


class ClientOperationInput(BaseModel):
    sender: str
    recipient: str
    amount: float
    payload: dict[str, Any] | None = None


class ClientOperation(BaseModel):
    operation_id: str
    sender: str
    recipient: str
    amount: float
    payload: dict[str, Any]
    status: OperationStatus
    created_at: datetime
    updated_at: datetime


class OperationTransition(BaseModel):
    from_status: OperationStatus | None
    to_status: OperationStatus
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    node_id: int | None = None
    protocol: ProtocolName
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class OperationTrace(BaseModel):
    operation: ClientOperation
    transitions: list[OperationTransition]


ALLOWED_TRANSITIONS: dict[OperationStatus | None, set[OperationStatus]] = {
    None: {OperationStatus.RECEIVED},
    OperationStatus.RECEIVED: {
        OperationStatus.BATCHED,
        OperationStatus.FAILED,
        OperationStatus.REJECTED,
    },
    OperationStatus.BATCHED: {
        OperationStatus.AVAILABLE,
        OperationStatus.FAILED,
        OperationStatus.REJECTED,
    },
    OperationStatus.AVAILABLE: {
        OperationStatus.PROPOSED,
        OperationStatus.FAILED,
        OperationStatus.REJECTED,
    },
    OperationStatus.PROPOSED: {
        OperationStatus.VOTED,
        OperationStatus.FAILED,
        OperationStatus.REJECTED,
    },
    OperationStatus.VOTED: {
        OperationStatus.QC_FORMED,
        OperationStatus.FAILED,
        OperationStatus.REJECTED,
    },
    OperationStatus.QC_FORMED: {
        OperationStatus.COMMITTED,
        OperationStatus.FAILED,
        OperationStatus.REJECTED,
    },
    OperationStatus.COMMITTED: {
        OperationStatus.EXECUTED,
        OperationStatus.FAILED,
        OperationStatus.REJECTED,
    },
    OperationStatus.EXECUTED: set(),
    OperationStatus.FAILED: set(),
    OperationStatus.REJECTED: set(),
}


class InMemoryOperationStore:
    def __init__(self) -> None:
        self._operations: dict[str, ClientOperation] = {}
        self._transitions: dict[str, list[OperationTransition]] = {}
        self._lock = threading.Lock()

    def create(self, input: ClientOperationInput) -> ClientOperation:
        now = datetime.now(timezone.utc)
        operation_id = str(uuid.uuid4())
        operation = ClientOperation(
            operation_id=operation_id,
            sender=input.sender,
            recipient=input.recipient,
            amount=input.amount,
            payload=input.payload or {},
            status=OperationStatus.RECEIVED,
            created_at=now,
            updated_at=now,
        )
        transition = OperationTransition(
            from_status=None,
            to_status=OperationStatus.RECEIVED,
            timestamp=now,
            node_id=None,
            protocol=ProtocolName.HOTSTUFF,
            message="Client operation received",
            details={},
        )
        with self._lock:
            self._operations[operation_id] = operation
            self._transitions[operation_id] = [transition]
        return operation

    def get(self, operation_id: str) -> ClientOperation:
        with self._lock:
            try:
                return self._operations[operation_id]
            except KeyError as exc:
                raise KeyError(f"Operation not found: {operation_id}") from exc

    def list(self, limit: int = 100) -> list[ClientOperation]:
        if limit < 0:
            raise ValueError("limit must be greater than or equal to 0")
        with self._lock:
            operations = list(self._operations.values())
            if limit == 0:
                return []
            return operations[-limit:]

    def transition(
        self,
        operation_id: str,
        to_status: OperationStatus,
        protocol: ProtocolName,
        message: str,
        node_id: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> ClientOperation:
        with self._lock:
            try:
                operation = self._operations[operation_id]
            except KeyError as exc:
                raise KeyError(f"Operation not found: {operation_id}") from exc

            from_status = operation.status
            allowed = ALLOWED_TRANSITIONS.get(from_status, set())
            if to_status not in allowed:
                raise ValueError(
                    f"Invalid operation transition: {from_status.value} -> {to_status.value}"
                )

            now = datetime.now(timezone.utc)
            updated = operation.model_copy(
                update={
                    "status": to_status,
                    "updated_at": now,
                }
            )
            transition = OperationTransition(
                from_status=from_status,
                to_status=to_status,
                timestamp=now,
                node_id=node_id,
                protocol=protocol,
                message=message,
                details=details or {},
            )
            self._operations[operation_id] = updated
            self._transitions[operation_id].append(transition)
            return updated

    def trace(self, operation_id: str) -> OperationTrace:
        with self._lock:
            try:
                operation = self._operations[operation_id]
                transitions = self._transitions[operation_id]
            except KeyError as exc:
                raise KeyError(f"Operation not found: {operation_id}") from exc
            return OperationTrace(
                operation=operation,
                transitions=list(transitions),
            )

    def clear(self) -> None:
        with self._lock:
            self._operations.clear()
            self._transitions.clear()


OPERATION_STORE = InMemoryOperationStore()
