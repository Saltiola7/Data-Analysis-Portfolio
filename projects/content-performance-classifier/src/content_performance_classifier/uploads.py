"""Bounded, runtime-only CSV parsing."""

from __future__ import annotations

from io import StringIO

import pandas as pd

from .contracts import MAX_INPUT_ROWS, InputValidationError

MAX_UPLOAD_BYTES = 5_000_000


def read_content_csv(
    payload: bytes,
    *,
    max_bytes: int = MAX_UPLOAD_BYTES,
    max_rows: int = MAX_INPUT_ROWS,
) -> pd.DataFrame:
    """Parse one bounded strict-UTF-8 CSV without filesystem or network access."""
    if not isinstance(payload, bytes):
        raise InputValidationError("CSV upload must be provided as bytes")
    if not payload:
        raise InputValidationError("CSV upload is empty")
    if len(payload) > max_bytes:
        raise InputValidationError("CSV upload exceeds the 5 MB limit")
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise InputValidationError("CSV upload must use valid UTF-8") from exc
    try:
        frame = pd.read_csv(StringIO(text))
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        raise InputValidationError("CSV upload is empty or malformed") from exc
    if frame.empty:
        raise InputValidationError("CSV upload must contain data rows")
    if len(frame) > max_rows:
        raise InputValidationError("CSV upload exceeds the 5,000-row limit")
    return frame
