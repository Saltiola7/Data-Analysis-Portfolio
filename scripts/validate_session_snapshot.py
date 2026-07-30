"""Validate deterministic source identity without comparing volatile Marimo output IDs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ERROR_MARKERS = (
    "MarimoExceptionRaisedError",
    "CellNotInitializedError",
    "ModuleNotFoundError",
    "No module named",
    "Traceback (most recent call last)",
)
PRIVATE_PATH_PATTERNS = (
    re.compile(r"/Users/[^/\s\"']+"),
    re.compile(r"[A-Za-z]:\\\\Users\\\\[^\\\s\"']+"),
)


class SessionValidationError(RuntimeError):
    """A committed or fresh Marimo session violated a preview contract."""


def _load_session(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SessionValidationError(f"invalid Marimo session JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise SessionValidationError(f"Marimo session root must be an object: {path}")
    return payload


def _source_signature(payload: dict[str, Any]) -> tuple[str, tuple[tuple[str, str], ...]]:
    metadata = payload.get("metadata")
    cells = payload.get("cells")
    if not isinstance(metadata, dict) or not isinstance(cells, list) or not cells:
        raise SessionValidationError("Marimo session lacks metadata or cells")
    script_hash = metadata.get("script_metadata_hash")
    if not isinstance(script_hash, str) or not script_hash:
        raise SessionValidationError("Marimo session lacks script metadata hash")

    signature: list[tuple[str, str]] = []
    for cell in cells:
        if not isinstance(cell, dict):
            raise SessionValidationError("Marimo session contains a malformed cell")
        cell_id = cell.get("id")
        code_hash = cell.get("code_hash")
        if not isinstance(cell_id, str) or not isinstance(code_hash, str):
            raise SessionValidationError("Marimo session cell lacks source identity")
        signature.append((cell_id, code_hash))
    if len({cell_id for cell_id, _ in signature}) != len(signature):
        raise SessionValidationError("Marimo session contains duplicate cell identities")
    return script_hash, tuple(signature)


def validate_session(path: Path, required_markers: tuple[str, ...]) -> None:
    """Validate structure, safe outputs, and expected synthetic evidence markers."""

    payload = _load_session(path)
    if payload.get("version") != "1":
        raise SessionValidationError(f"unsupported Marimo session version: {path}")
    _source_signature(payload)

    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    for marker in ERROR_MARKERS:
        if marker in serialized:
            raise SessionValidationError(f"Marimo session contains {marker!r}: {path}")
    for pattern in PRIVATE_PATH_PATTERNS:
        if pattern.search(serialized):
            raise SessionValidationError(f"Marimo session contains a private local path: {path}")
    for marker in required_markers:
        if marker not in serialized:
            raise SessionValidationError(
                f"Marimo session lacks required marker {marker!r}: {path}"
            )


def compare_session_sources(committed: Path, fresh: Path) -> None:
    """Compare only stable script and cell source hashes."""

    committed_signature = _source_signature(_load_session(committed))
    fresh_signature = _source_signature(_load_session(fresh))
    if committed_signature != fresh_signature:
        raise SessionValidationError("committed and fresh session source hashes differ")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("committed", type=Path)
    parser.add_argument("--fresh", type=Path)
    parser.add_argument("--marker", action="append", default=[])
    args = parser.parse_args()
    markers = tuple(args.marker)
    validate_session(args.committed, markers)
    if args.fresh is not None:
        validate_session(args.fresh, markers)
        compare_session_sources(args.committed, args.fresh)
    print("Marimo session validation passed")


if __name__ == "__main__":
    main()
