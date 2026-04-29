from __future__ import annotations

import importlib
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "proto" / "bft.proto").exists():
            return parent
    raise RuntimeError("Cannot locate repository root containing proto/bft.proto")


def _default_proto_path() -> Path:
    return _repo_root() / "proto" / "bft.proto"


def compile_proto_to_tmp(proto_path: Path | None = None) -> Path:
    """Compile proto/bft.proto into a temporary generated module directory."""

    proto = (proto_path or _default_proto_path()).resolve()
    if not proto.exists():
        raise RuntimeError(f"Proto file not found: {proto}")

    try:
        from grpc_tools import protoc
    except ImportError as exc:
        raise RuntimeError(
            "grpc_tools is required for gRPC runtime demo. Install requirements-api.txt."
        ) from exc

    generated_dir = Path(tempfile.mkdtemp(prefix="bft_generated_grpc_"))
    proto_root = proto.parent.resolve()
    result = protoc.main(
        [
            "grpc_tools.protoc",
            f"-I{proto_root}",
            f"--python_out={generated_dir}",
            f"--grpc_python_out={generated_dir}",
            str(proto),
        ]
    )
    if result != 0:
        raise RuntimeError(f"grpc_tools.protoc failed with exit code {result}")

    generated_str = str(generated_dir)
    if generated_str not in sys.path:
        sys.path.insert(0, generated_str)
    return generated_dir


def load_generated_modules(generated_dir: Path) -> tuple[Any, Any]:
    generated_str = str(generated_dir)
    if generated_str not in sys.path:
        sys.path.insert(0, generated_str)

    bft_pb2: ModuleType = importlib.import_module("bft_pb2")
    bft_pb2_grpc: ModuleType = importlib.import_module("bft_pb2_grpc")
    return bft_pb2, bft_pb2_grpc
