"""Bounded CSV upload parsing for the interactive notebook."""

from __future__ import annotations

import io

import pandas as pd


class UploadError(ValueError):
    """Raised when an uploaded CSV cannot be accepted safely."""


def read_csv_upload(
    payload: bytes,
    *,
    max_bytes: int = 2_000_000,
    max_rows: int = 10_000,
) -> pd.DataFrame:
    """Parse a bounded UTF-8 CSV without retaining or echoing its payload."""

    if not isinstance(payload, bytes):
        raise UploadError("CSV upload must be provided as bytes")
    if not payload:
        raise UploadError("CSV upload is empty")
    if len(payload) > max_bytes:
        raise UploadError(f"CSV upload exceeds the maximum of {max_bytes:,} bytes")

    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise UploadError("CSV upload must use valid UTF-8 encoding") from exc

    try:
        frame = pd.read_csv(io.StringIO(text))
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        raise UploadError("CSV upload could not be parsed") from exc

    if frame.empty:
        raise UploadError("CSV upload contains no data rows")
    if len(frame) > max_rows:
        raise UploadError(f"CSV upload exceeds the maximum of {max_rows:,} rows")
    return frame
