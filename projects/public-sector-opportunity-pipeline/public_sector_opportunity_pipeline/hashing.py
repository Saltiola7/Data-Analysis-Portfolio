"""Stable content identity helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd


def stable_json(value: object) -> str:
    """Serialize supported public values deterministically."""

    return json.dumps(
        _json_value(value),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def content_hash(value: object) -> str:
    """Return a SHA-256 identity for deterministic JSON content."""

    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def dataframe_hash(frame: pd.DataFrame) -> str:
    """Hash column order and row records of a pre-sorted frame."""

    payload = {
        "columns": list(frame.columns),
        "records": frame.where(pd.notna(frame), None).to_dict("records"),
    }
    return content_hash(payload)


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return [_json_value(item) for item in value]
    if hasattr(value, "item"):
        return _json_value(value.item())
    return str(value)
