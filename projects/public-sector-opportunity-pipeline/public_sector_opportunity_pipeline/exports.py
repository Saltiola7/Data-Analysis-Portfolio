"""Explicit safe exports for tabular and manifest evidence."""

from __future__ import annotations

import json

import pandas as pd

from public_sector_opportunity_pipeline.models import RunManifest

SPREADSHEET_FORMULA_PREFIXES = ("=", "+", "-", "@")
SPREADSHEET_CONTROL_PREFIXES = ("\t", "\r", "\n")


def dataframe_to_safe_csv(frame: pd.DataFrame) -> str:
    """Serialize a copy while neutralizing spreadsheet formula strings."""

    safe_frame = frame.copy(deep=True)
    for column in safe_frame.columns:
        safe_frame[column] = safe_frame[column].map(_escape_spreadsheet_formula)
    return safe_frame.to_csv(index=False, lineterminator="\n")


def manifest_to_json(manifest: RunManifest) -> str:
    """Serialize manifest with stable ordering and a trailing newline."""

    return (
        json.dumps(
            manifest.as_dict(),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _escape_spreadsheet_formula(value: object) -> object:
    if isinstance(value, str) and (
        value.startswith(SPREADSHEET_CONTROL_PREFIXES)
        or value.lstrip().startswith(SPREADSHEET_FORMULA_PREFIXES)
    ):
        return f"'{value}"
    return value
