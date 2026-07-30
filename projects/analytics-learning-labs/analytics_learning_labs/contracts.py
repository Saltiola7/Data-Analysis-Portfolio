"""Schema, grain, and boundary contracts for synthetic learning-lab data."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

import pandas as pd

MAXIMUM_FIXTURE_ROWS = 5_000


@dataclass(frozen=True)
class FixtureContract:
    """Required columns, observation grain, and allocation bound for a fixture."""

    slug: str
    required_columns: tuple[str, ...]
    grain_columns: tuple[str, ...]
    maximum_rows: int


@dataclass(frozen=True)
class AnalysisResult:
    """Display-ready evidence returned by one learning-lab analysis."""

    lab_slug: str
    grain: str
    metrics: Mapping[str, str | int | float]
    primary_table: pd.DataFrame
    secondary_table: pd.DataFrame | None
    notes: tuple[str, ...]


AIRLINE_CONTRACT = FixtureContract(
    slug="airline",
    required_columns=(
        "flight_id",
        "carrier",
        "route",
        "arrival_delay_minutes",
        "carrier_delay_minutes",
        "late_aircraft_delay_minutes",
        "cancelled",
    ),
    grain_columns=("flight_id",),
    maximum_rows=MAXIMUM_FIXTURE_ROWS,
)

COHORT_CONTRACT = FixtureContract(
    slug="cohort",
    required_columns=(
        "record_id",
        "profile_key",
        "age_band",
        "exposure_score",
        "genetic_risk_score",
        "obesity_score",
        "risk_band",
    ),
    grain_columns=("record_id",),
    maximum_rows=MAXIMUM_FIXTURE_ROWS,
)

RESTAURANT_CONTRACT = FixtureContract(
    slug="restaurant",
    required_columns=(
        "record_id",
        "location_label",
        "country",
        "region",
        "latitude",
        "longitude",
    ),
    grain_columns=("record_id",),
    maximum_rows=MAXIMUM_FIXTURE_ROWS,
)

STREAMING_CONTRACT = FixtureContract(
    slug="streaming",
    required_columns=(
        "title_id",
        "release_year",
        "duration_minutes",
        "genre",
        "content_type",
    ),
    grain_columns=("title_id",),
    maximum_rows=MAXIMUM_FIXTURE_ROWS,
)

SPORTS_CONTRACT = FixtureContract(
    slug="sports",
    required_columns=(
        "event_id",
        "athlete_id",
        "team",
        "continent",
        "weight_class",
        "medal",
    ),
    grain_columns=("event_id",),
    maximum_rows=MAXIMUM_FIXTURE_ROWS,
)

ANALYTICAL_DIMENSIONS = {
    AIRLINE_CONTRACT.slug: ("carrier", "route"),
    COHORT_CONTRACT.slug: ("profile_key", "age_band", "risk_band"),
    RESTAURANT_CONTRACT.slug: ("location_label", "country", "region"),
    STREAMING_CONTRACT.slug: ("genre", "content_type"),
    SPORTS_CONTRACT.slug: ("athlete_id", "team", "continent", "weight_class"),
}


def _require_numeric(
    frame: pd.DataFrame,
    columns: tuple[str, ...],
) -> pd.DataFrame:
    non_numeric = [
        column
        for column in columns
        if pd.api.types.is_bool_dtype(frame[column])
        or not pd.api.types.is_numeric_dtype(frame[column])
    ]
    if non_numeric:
        raise ValueError(f"numeric dtype required for {', '.join(non_numeric)}")
    numeric = frame.loc[:, list(columns)]
    if numeric.isna().any(axis=None):
        raise ValueError(f"numeric boundary failed for {', '.join(columns)}")
    if not numeric.map(lambda value: math.isfinite(float(value))).all(axis=None):
        raise ValueError(f"finite numeric boundary failed for {', '.join(columns)}")
    return numeric


def _require_boolean(frame: pd.DataFrame, column: str) -> None:
    if not pd.api.types.is_bool_dtype(frame[column]):
        raise ValueError(f"{column} must contain boolean values")
    if frame[column].isna().any():
        raise ValueError(f"{column} boolean values cannot be null")


def _require_analytical_dimensions(
    frame: pd.DataFrame,
    columns: tuple[str, ...],
) -> None:
    for column in columns:
        values = frame[column]
        if values.isna().any():
            raise ValueError(f"analytical dimension {column} cannot be null")
        if values.astype("string").str.strip().eq("").any():
            raise ValueError(f"analytical dimension {column} cannot be blank")


def _validate_airline(frame: pd.DataFrame) -> None:
    _require_boolean(frame, "cancelled")
    components = _require_numeric(
        frame,
        ("carrier_delay_minutes", "late_aircraft_delay_minutes"),
    )
    if components.lt(0).any(axis=None):
        raise ValueError("airline delay components must be non-negative")
    _require_numeric(frame, ("arrival_delay_minutes",))
    cancelled_delays = frame.loc[
        frame["cancelled"],
        (
            "arrival_delay_minutes",
            "carrier_delay_minutes",
            "late_aircraft_delay_minutes",
        ),
    ]
    if not cancelled_delays.eq(0).all(axis=None):
        raise ValueError("cancelled flights must use zero delay placeholders")


def _validate_cohort(frame: pd.DataFrame) -> None:
    scores = _require_numeric(
        frame,
        ("exposure_score", "genetic_risk_score", "obesity_score"),
    )
    if scores.lt(0).any(axis=None) or scores.gt(10).any(axis=None):
        raise ValueError("cohort ordinal scores must be between 0 and 10")
    allowed_risk_bands = {"low", "medium", "high"}
    if not set(frame["risk_band"].astype(str).str.casefold()).issubset(allowed_risk_bands):
        raise ValueError("risk_band must be low, medium, or high")
    profile_attributes = [
        "age_band",
        "exposure_score",
        "genetic_risk_score",
        "obesity_score",
        "risk_band",
    ]
    normalized_profiles = frame.loc[:, ["profile_key", *profile_attributes]].copy()
    normalized_profiles["risk_band"] = (
        normalized_profiles["risk_band"].astype("string").str.casefold()
    )
    profile_variants = normalized_profiles.groupby("profile_key", observed=True)[
        profile_attributes
    ].nunique(dropna=False)
    if profile_variants.gt(1).any(axis=None):
        raise ValueError("duplicate profile records must agree on profile attributes")


def _validate_restaurant(frame: pd.DataFrame) -> None:
    for column in ("latitude", "longitude"):
        if pd.api.types.is_bool_dtype(frame[column]) or not pd.api.types.is_numeric_dtype(
            frame[column]
        ):
            raise ValueError(f"numeric dtype required for {column}")
        resolved_values = frame[column].dropna()
        if not resolved_values.map(lambda value: math.isfinite(float(value))).all():
            raise ValueError(f"{column} must be finite when present")
    if not frame["latitude"].dropna().between(-90, 90).all():
        raise ValueError("latitude must be between -90 and 90")
    if not frame["longitude"].dropna().between(-180, 180).all():
        raise ValueError("longitude must be between -180 and 180")


def _validate_streaming(frame: pd.DataFrame) -> None:
    values = _require_numeric(frame, ("release_year", "duration_minutes"))
    if not values["release_year"].between(1900, 2026).all():
        raise ValueError("release_year must be between 1900 and 2026")
    if not values["duration_minutes"].gt(0).all():
        raise ValueError("duration_minutes must be positive")


def _validate_sports(frame: pd.DataFrame) -> None:
    _require_boolean(frame, "medal")
    athlete_dimensions = frame.groupby("athlete_id", observed=True)[
        ["team", "continent", "weight_class"]
    ].nunique(dropna=False)
    if athlete_dimensions.gt(1).any(axis=None):
        raise ValueError("athlete identity dimensions must remain stable across events")
    if frame.groupby("team", observed=True)["continent"].nunique(dropna=False).gt(1).any():
        raise ValueError("each team must map to exactly one continent")


def validate_fixture(frame: pd.DataFrame, contract: FixtureContract) -> None:
    """Fail closed when a frame violates its declared schema, grain, or bounds."""

    if not isinstance(frame, pd.DataFrame):
        raise TypeError("fixture must be a pandas DataFrame")
    if frame.empty:
        raise ValueError("fixture must contain at least one row")
    if len(frame) > contract.maximum_rows:
        raise ValueError(f"fixture exceeds maximum of {contract.maximum_rows:,} rows")

    missing = [column for column in contract.required_columns if column not in frame.columns]
    if missing:
        raise ValueError(f"fixture is missing required columns: {', '.join(missing)}")

    grain = frame.loc[:, list(contract.grain_columns)]
    if grain.isna().any(axis=None):
        raise ValueError("fixture grain columns cannot contain null values")
    if grain.duplicated().any():
        raise ValueError("fixture grain columns must be unique")

    dimensions = ANALYTICAL_DIMENSIONS.get(contract.slug)
    if dimensions is not None:
        _require_analytical_dimensions(frame, dimensions)

    validators = {
        AIRLINE_CONTRACT.slug: _validate_airline,
        COHORT_CONTRACT.slug: _validate_cohort,
        RESTAURANT_CONTRACT.slug: _validate_restaurant,
        STREAMING_CONTRACT.slug: _validate_streaming,
        SPORTS_CONTRACT.slug: _validate_sports,
    }
    validator = validators.get(contract.slug)
    if validator is not None:
        validator(frame)
