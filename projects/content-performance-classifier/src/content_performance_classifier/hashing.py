"""Stable identities for fixtures, three-way splits, probabilities, and models."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd


def hash_bytes(payload: bytes) -> str:
    """Return a SHA-256 hexadecimal digest."""
    return hashlib.sha256(payload).hexdigest()


def hash_frame(frame: pd.DataFrame) -> str:
    """Hash a frame with stable column order, row order, and scalar encoding."""
    canonical = frame.to_csv(index=False, lineterminator="\n", float_format="%.12g")
    return hash_bytes(canonical.encode("utf-8"))


def hash_strings(values: Sequence[str]) -> str:
    """Hash an ordered string sequence."""
    return hash_bytes(json.dumps(list(values), separators=(",", ":")).encode())


def hash_probabilities(values: np.ndarray) -> str:
    """Hash deterministic float64 probability bytes."""
    canonical = np.asarray(values, dtype="<f8")
    return hash_bytes(canonical.tobytes())


def hash_mapping(value: Mapping[str, Any]) -> str:
    """Hash JSON-compatible model lineage."""
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=_json_default)
    return hash_bytes(payload.encode())


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"unsupported hash value: {type(value).__name__}")
