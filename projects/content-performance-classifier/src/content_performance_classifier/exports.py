"""Safe user-triggered evidence exports."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from .evaluation import evaluate_reserved_test
from .models import EvaluationResult, ModelArtifact

DANGEROUS_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def predictions_to_safe_csv(result: EvaluationResult) -> str:
    """Serialize predictions while neutralizing spreadsheet formula strings."""
    safe = result.predictions.copy(deep=True)
    for column in safe.select_dtypes(include=["object", "string"]).columns:
        safe[column] = safe[column].map(_neutralize_formula_string)
    return safe.to_csv(index=False, lineterminator="\n")


def audit_to_json(artifact: ModelArtifact, result: EvaluationResult) -> str:
    """Serialize aggregate lineage without raw rows, identifiers, or category text."""
    reserved_test = evaluate_reserved_test(artifact)
    audit = {
        "schema_version": "content-classifier-audit-v2",
        "fixture": {
            "version": artifact.fixture_version,
            "hash": artifact.fixture_hash,
        },
        "training": {
            "seed": artifact.seed,
            "source_hash": artifact.source_hash,
            "split_identity": artifact.split_identity,
            "model_hash": artifact.model_hash,
            "train_rows": len(artifact.train_ids),
            "validation_rows": len(artifact.validation_ids),
            "test_rows": len(artifact.test_ids),
            "feature_columns": list(artifact.feature_columns),
            "parameters": artifact.model_parameters,
        },
        "evaluation": {
            "partition": result.partition,
            "threshold": result.threshold,
            "probability_hash": result.probability_hash,
            "metrics": result.metrics,
            "validation_slices": _pseudonymized_slice_records(result.slices),
            "validation_calibration": _records_without_nan(result.calibration),
            "slice_label_policy": (
                "Category values are replaced with non-reversible, per-dimension "
                "ordinal pseudonyms."
            ),
            "reserved_test": {
                "partition": reserved_test.partition,
                "threshold": reserved_test.threshold,
                "threshold_selection_metric": artifact.threshold_selection_metric,
                "probability_hash": reserved_test.probability_hash,
                "metrics": reserved_test.metrics,
                "slices": _pseudonymized_slice_records(reserved_test.slices),
                "calibration": _records_without_nan(reserved_test.calibration),
            },
        },
    }
    return (
        json.dumps(
            audit,
            sort_keys=True,
            indent=2,
            default=_json_default,
            allow_nan=False,
        )
        + "\n"
    )


def _neutralize_formula_string(value: object) -> object:
    if isinstance(value, str) and value.lstrip(" ").startswith(DANGEROUS_FORMULA_PREFIXES):
        return f"'{value}"
    return value


def _records_without_nan(frame: pd.DataFrame) -> list[dict[str, object]]:
    safe = frame.astype(object).where(frame.notna(), None)
    return safe.to_dict(orient="records")


def _pseudonymized_slice_records(frame: pd.DataFrame) -> list[dict[str, object]]:
    """Remove arbitrary uploaded category text while retaining slice evidence."""
    safe = frame.copy(deep=True)
    for dimension in safe["dimension"].drop_duplicates().tolist():
        mask = safe["dimension"] == dimension
        values = safe.loc[mask, "value"].drop_duplicates().tolist()
        aliases = {value: f"category-{index:03d}" for index, value in enumerate(values, start=1)}
        safe.loc[mask, "value"] = safe.loc[mask, "value"].map(aliases)
    return _records_without_nan(safe)


def _json_default(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if pd.isna(value):
        return None
    raise TypeError(f"cannot serialize {type(value).__name__}")
