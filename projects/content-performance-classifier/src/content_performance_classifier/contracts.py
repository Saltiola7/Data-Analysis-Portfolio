"""Input contracts and explicit leakage boundary."""

from __future__ import annotations

from types import MappingProxyType

import pandas as pd

MAX_INPUT_ROWS = 5_000
MIN_INPUT_ROWS = 20
MAX_CATEGORY_CARDINALITY = 50
MAX_CATEGORY_LENGTH = 100
EXPECTED_TARGET_CLASSES = 2
MIN_ROWS_PER_CLASS = 5

TOPIC_FAMILIES = frozenset(
    {
        "analytics",
        "commerce",
        "operations",
        "strategy",
        "technical",
    }
)
CONTENT_TYPES = frozenset({"case_study", "comparison", "guide", "reference", "tutorial"})

CATEGORICAL_FEATURES = ("topic_family", "content_type")
NUMERIC_FEATURES = (
    "word_count",
    "readability_score",
    "age_days",
    "internal_link_count",
    "entity_count",
    "query_coverage",
    "update_cadence",
)
FEATURE_ALLOWLIST = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET_COLUMN = "high_engagement"
IDENTIFIER_COLUMN = "content_id"
CONTENT_COLUMNS = (IDENTIFIER_COLUMN, *FEATURE_ALLOWLIST, TARGET_COLUMN)

NUMERIC_RANGES = MappingProxyType(
    {
        "word_count": (200, 5_000),
        "readability_score": (0, 100),
        "age_days": (0, 2_000),
        "internal_link_count": (0, 100),
        "entity_count": (0, 100),
        "query_coverage": (0, 1),
        "update_cadence": (0, 24),
    }
)


class InputValidationError(ValueError):
    """Raised when content data violates the closed training contract."""


def validate_training_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Copy and validate one-row-per-content-item training data."""
    if not isinstance(frame, pd.DataFrame):
        raise InputValidationError("training input must be a pandas DataFrame")
    if len(frame) > MAX_INPUT_ROWS:
        raise InputValidationError("training input exceeds the 5,000-row limit")
    if len(frame) < MIN_INPUT_ROWS:
        raise InputValidationError(f"training input requires at least {MIN_INPUT_ROWS} data rows")

    missing = [column for column in CONTENT_COLUMNS if column not in frame.columns]
    if missing:
        raise InputValidationError(f"missing required columns: {', '.join(missing)}")

    validated = frame.copy(deep=True)
    required = validated.loc[:, CONTENT_COLUMNS]
    if required.isna().any().any():
        columns = required.columns[required.isna().any()].tolist()
        raise InputValidationError(f"null values are not allowed in: {', '.join(columns)}")

    _validate_identifiers(validated)
    _validate_categories(validated)
    _validate_numeric_features(validated)
    _validate_target(validated)
    return validated


def _validate_identifiers(frame: pd.DataFrame) -> None:
    identifiers = frame[IDENTIFIER_COLUMN]
    if not identifiers.map(lambda value: isinstance(value, str) and bool(value.strip())).all():
        raise InputValidationError("content_id values must be non-empty strings")
    if not identifiers.is_unique:
        raise InputValidationError("content_id values must be unique")


def _validate_categories(frame: pd.DataFrame) -> None:
    for column in CATEGORICAL_FEATURES:
        values = frame[column]
        if not values.map(lambda value: isinstance(value, str) and bool(value.strip())).all():
            raise InputValidationError(f"{column} values must be non-empty strings")
        if values.nunique() > MAX_CATEGORY_CARDINALITY:
            raise InputValidationError(
                f"{column} exceeds {MAX_CATEGORY_CARDINALITY} distinct values"
            )
        if values.str.len().max() > MAX_CATEGORY_LENGTH:
            raise InputValidationError(f"{column} values exceed {MAX_CATEGORY_LENGTH} characters")


def _validate_numeric_features(frame: pd.DataFrame) -> None:
    for column, (lower, upper) in NUMERIC_RANGES.items():
        numeric = pd.to_numeric(frame[column], errors="coerce")
        if numeric.isna().any() or not numeric.between(lower, upper).all():
            raise InputValidationError(
                f"{column} must contain numeric values from {lower} through {upper}"
            )
        frame[column] = numeric


def _validate_target(frame: pd.DataFrame) -> None:
    target = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    if target.isna().any() or not target.isin([0, 1]).all():
        raise InputValidationError("high_engagement must contain only binary 0 or 1 values")
    frame[TARGET_COLUMN] = target.astype("int8")

    class_counts = frame[TARGET_COLUMN].value_counts()
    if (
        len(class_counts) != EXPECTED_TARGET_CLASSES
        or int(class_counts.min()) < MIN_ROWS_PER_CLASS
    ):
        raise InputValidationError(
            "high_engagement requires both classes with at least five rows each"
        )
