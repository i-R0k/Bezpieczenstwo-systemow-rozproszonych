from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


def _normalize(data: Any) -> Any:
    if isinstance(data, BaseModel):
        return data.model_dump(mode="json")
    if isinstance(data, datetime):
        return data.isoformat()
    if isinstance(data, Enum):
        return data.value
    if isinstance(data, dict):
        return {str(key): _normalize(value) for key, value in data.items()}
    if isinstance(data, (list, tuple)):
        return [_normalize(item) for item in data]
    return data


def canonical_json_bytes(data: Any) -> bytes:
    return json.dumps(
        _normalize(data),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
