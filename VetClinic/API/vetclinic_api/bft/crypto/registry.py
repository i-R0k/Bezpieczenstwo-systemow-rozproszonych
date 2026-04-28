from __future__ import annotations

import threading

from vetclinic_api.bft.crypto.keys import NodeKeyPair, generate_node_keypair


class InMemoryNodeKeyRegistry:
    def __init__(self) -> None:
        self._keys: dict[int, NodeKeyPair] = {}
        self._lock = threading.Lock()

    def register_keypair(self, keypair: NodeKeyPair) -> NodeKeyPair:
        with self._lock:
            self._keys[keypair.node_id] = keypair
            return keypair.model_copy(update={"private_key_b64": None})

    def register_public_key(self, node_id: int, public_key_b64: str) -> NodeKeyPair:
        keypair = NodeKeyPair(
            node_id=node_id,
            public_key_b64=public_key_b64,
            private_key_b64=None,
        )
        with self._lock:
            self._keys[node_id] = keypair
            return keypair

    def get_public_key(self, node_id: int) -> str:
        with self._lock:
            try:
                return self._keys[node_id].public_key_b64
            except KeyError as exc:
                raise KeyError(f"Public key not found for node {node_id}") from exc

    def get_private_key(self, node_id: int) -> str:
        with self._lock:
            try:
                private_key = self._keys[node_id].private_key_b64
            except KeyError as exc:
                raise KeyError(f"Private key not found for node {node_id}") from exc
            if private_key is None:
                raise KeyError(f"Private key not available for node {node_id}")
            return private_key

    def public_keys(self) -> dict[int, str]:
        with self._lock:
            return {
                node_id: keypair.public_key_b64
                for node_id, keypair in self._keys.items()
            }

    def ensure_demo_keys(self, node_ids: list[int]) -> list[NodeKeyPair]:
        with self._lock:
            for node_id in node_ids:
                if node_id not in self._keys:
                    self._keys[node_id] = generate_node_keypair(node_id)
            return [
                self._keys[node_id].model_copy(update={"private_key_b64": None})
                for node_id in node_ids
            ]

    def clear(self) -> None:
        with self._lock:
            self._keys.clear()


NODE_KEY_REGISTRY = InMemoryNodeKeyRegistry()
