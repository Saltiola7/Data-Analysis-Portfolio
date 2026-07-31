"""Public result types and exceptions for the wellness pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


class SchemaError(ValueError):
    """Raised when an input table does not satisfy its required schema."""


class NormalizationError(ValueError):
    """Raised when a numeric value or unit cannot be normalized safely."""

    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True)
class SyntheticFixture:
    """Deterministic synthetic inputs plus generator provenance."""

    participants: pd.DataFrame
    programs: pd.DataFrame
    daily_signals: pd.DataFrame
    interventions: pd.DataFrame
    seed: int
    generator_version: str


@dataclass(frozen=True)
class PipelineResult:
    """Curated data, rejected rows, and deterministic audit evidence."""

    participant_days: pd.DataFrame
    rejected_records: pd.DataFrame
    audit: dict[str, Any]


@dataclass(frozen=True)
class SourceProfile:
    """Aggregate source metadata without raw values."""

    row_count: int
    column_count: int
    required_field_null_counts: dict[str, int]
    duplicate_key_count: int
    accepted_count: int
    rejected_count: int
