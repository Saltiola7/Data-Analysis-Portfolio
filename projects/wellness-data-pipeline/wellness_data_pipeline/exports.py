"""Safe explicit exports for user-controlled tabular data."""

from __future__ import annotations

import pandas as pd

SPREADSHEET_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _escape_spreadsheet_formula(value: object) -> object:
    if isinstance(value, str) and value.startswith(SPREADSHEET_FORMULA_PREFIXES):
        return f"'{value}"
    return value


def dataframe_to_safe_csv(frame: pd.DataFrame) -> str:
    """Serialize a copy while neutralizing spreadsheet formula strings."""

    safe_frame = frame.copy(deep=True)
    for column in safe_frame.columns:
        safe_frame[column] = safe_frame[column].map(_escape_spreadsheet_formula)
    return safe_frame.to_csv(index=False, lineterminator="\n")
