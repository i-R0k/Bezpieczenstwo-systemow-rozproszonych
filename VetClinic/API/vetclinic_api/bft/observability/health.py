from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class BftComponentHealth(BaseModel):
    name: str
    status: str
    details: dict[str, Any] = Field(default_factory=dict)


class BftSystemHealth(BaseModel):
    status: str
    components: list[BftComponentHealth]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HealthService:
    def __init__(
        self,
        *,
        operation_store,
        narwhal_store,
        hotstuff_store,
        swim_store,
        fault_store,
        checkpoint_store,
        recovery_store,
        node_key_registry,
        self_node_id: int = 1,
    ) -> None:
        self.operation_store = operation_store
        self.narwhal_store = narwhal_store
        self.hotstuff_store = hotstuff_store
        self.swim_store = swim_store
        self.fault_store = fault_store
        self.checkpoint_store = checkpoint_store
        self.recovery_store = recovery_store
        self.node_key_registry = node_key_registry
        self.self_node_id = self_node_id

    def check_operations(self) -> BftComponentHealth:
        return self._safe("operations", lambda: {"operations": len(self.operation_store.list(limit=10000))})

    def check_narwhal(self) -> BftComponentHealth:
        return self._safe("narwhal", lambda: {"dag_vertices": self.narwhal_store.get_dag().total_batches})

    def check_hotstuff(self) -> BftComponentHealth:
        return self._safe("hotstuff", lambda: {"view": self.hotstuff_store.current_view().view})

    def check_swim(self) -> BftComponentHealth:
        def details():
            status = self.swim_store.status(self.self_node_id)
            result = status.model_dump(mode="json")
            if not status.members:
                return "warning", result
            return "ok", result
        return self._safe_status("swim", details)

    def check_faults(self) -> BftComponentHealth:
        return self._safe("faults", lambda: {"rules": len(self.fault_store.list_rules())})

    def check_checkpointing(self) -> BftComponentHealth:
        return self._safe("checkpointing", lambda: {"checkpoints": len(self.checkpoint_store.list_certificates(limit=10000))})

    def check_recovery(self) -> BftComponentHealth:
        return self._safe("recovery", lambda: {"recovered_nodes": len(self.recovery_store.status().recovered_nodes)})

    def check_crypto(self) -> BftComponentHealth:
        def details():
            keys = self.node_key_registry.public_keys()
            return ("ok" if keys else "warning"), {"registered_public_keys": len(keys)}
        return self._safe_status("crypto", details)

    def check_all(self) -> BftSystemHealth:
        components = [
            self.check_operations(),
            self.check_narwhal(),
            self.check_hotstuff(),
            self.check_swim(),
            self.check_faults(),
            self.check_checkpointing(),
            self.check_recovery(),
            self.check_crypto(),
        ]
        if any(component.status == "error" for component in components):
            status = "error"
        elif any(component.status == "warning" for component in components):
            status = "warning"
        else:
            status = "ok"
        return BftSystemHealth(status=status, components=components)

    @staticmethod
    def _safe(name: str, fn) -> BftComponentHealth:
        try:
            return BftComponentHealth(name=name, status="ok", details=fn())
        except Exception as exc:
            return BftComponentHealth(name=name, status="error", details={"error": str(exc)})

    @staticmethod
    def _safe_status(name: str, fn) -> BftComponentHealth:
        try:
            status, details = fn()
            return BftComponentHealth(name=name, status=status, details=details)
        except Exception as exc:
            return BftComponentHealth(name=name, status="error", details={"error": str(exc)})
