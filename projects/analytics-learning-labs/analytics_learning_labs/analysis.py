"""Validated analyses over deterministic synthetic learning-lab fixtures."""

from __future__ import annotations

import math

import pandas as pd

from analytics_learning_labs.contracts import (
    AIRLINE_CONTRACT,
    COHORT_CONTRACT,
    RESTAURANT_CONTRACT,
    SPORTS_CONTRACT,
    STREAMING_CONTRACT,
    AnalysisResult,
    validate_fixture,
)

ON_TIME_DELAY_MINUTES = 15
MINIMUM_ASSOCIATION_LEVELS = 2


def _rounded(value: object, digits: int = 3) -> float:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError("analysis metric must be finite")
    return round(numeric, digits)


def analyze_airline_delays(frame: pd.DataFrame) -> AnalysisResult:
    """Summarize delay quality by fictional carrier and route."""

    validate_fixture(frame, AIRLINE_CONTRACT)
    evidence = frame.copy(deep=True)
    evidence["on_time"] = (~evidence["cancelled"]) & (
        evidence["arrival_delay_minutes"] <= ON_TIME_DELAY_MINUTES
    )
    evidence["completed"] = ~evidence["cancelled"]
    for column in (
        "arrival_delay_minutes",
        "carrier_delay_minutes",
        "late_aircraft_delay_minutes",
    ):
        evidence[f"completed_{column}"] = evidence[column].mask(evidence["cancelled"])

    carrier_summary = (
        evidence.groupby("carrier", as_index=False, observed=True)
        .agg(
            flights=("flight_id", "count"),
            completed_flights=("completed", "sum"),
            cancelled_flights=("cancelled", "sum"),
            mean_arrival_delay_minutes=("completed_arrival_delay_minutes", "mean"),
            mean_carrier_delay_minutes=("completed_carrier_delay_minutes", "mean"),
            mean_late_aircraft_delay_minutes=(
                "completed_late_aircraft_delay_minutes",
                "mean",
            ),
            on_time_rate=("on_time", "mean"),
        )
        .sort_values(["on_time_rate", "carrier"], ascending=[False, True])
        .reset_index(drop=True)
    )
    carrier_summary["mean_arrival_delay_minutes"] = carrier_summary[
        "mean_arrival_delay_minutes"
    ].round(1)
    carrier_summary["mean_carrier_delay_minutes"] = carrier_summary[
        "mean_carrier_delay_minutes"
    ].round(1)
    carrier_summary["mean_late_aircraft_delay_minutes"] = carrier_summary[
        "mean_late_aircraft_delay_minutes"
    ].round(1)
    carrier_summary["on_time_rate_percent"] = (carrier_summary.pop("on_time_rate") * 100).round(1)

    route_summary = (
        evidence.groupby("route", as_index=False, observed=True)
        .agg(
            flights=("flight_id", "count"),
            completed_flights=("completed", "sum"),
            cancelled_flights=("cancelled", "sum"),
            mean_arrival_delay_minutes=("completed_arrival_delay_minutes", "mean"),
        )
        .sort_values(["flights", "route"], ascending=[False, True])
        .reset_index(drop=True)
    )
    route_summary["mean_arrival_delay_minutes"] = route_summary[
        "mean_arrival_delay_minutes"
    ].round(1)

    return AnalysisResult(
        lab_slug="airline",
        grain="one fictional flight",
        metrics={
            "source_flights": len(evidence),
            "carriers": int(evidence["carrier"].nunique()),
            "cancellation_rate_percent": _rounded(
                evidence["cancelled"].mean() * 100,
                1,
            ),
            "overall_on_time_rate_percent": _rounded(
                evidence["on_time"].mean() * 100,
                1,
            ),
        },
        primary_table=carrier_summary,
        secondary_table=route_summary,
        notes=(
            "All carriers, routes, flights, and delay values are fictional.",
            "On time means not cancelled and no more than 15 minutes late.",
            "Mean delay values use completed flights only; cancellations remain in "
            "flight and cancellation denominators.",
        ),
    )


def analyze_synthetic_cohort(frame: pd.DataFrame) -> AnalysisResult:
    """Deduplicate fictional profiles before descriptive ordinal association."""

    validate_fixture(frame, COHORT_CONTRACT)
    evidence = frame.copy(deep=True)
    evidence["risk_band"] = evidence["risk_band"].astype("string").str.casefold()
    profile_counts = (
        evidence.groupby("profile_key", as_index=False, observed=True)
        .agg(record_count=("record_id", "count"))
        .sort_values(["record_count", "profile_key"], ascending=[False, True])
        .reset_index(drop=True)
    )
    unique_profiles = (
        evidence.sort_values("record_id")
        .drop_duplicates("profile_key", keep="first")
        .reset_index(drop=True)
    )

    risk_order = {"low": 0, "medium": 1, "high": 2}
    composite = unique_profiles[["exposure_score", "genetic_risk_score", "obesity_score"]].mean(
        axis=1
    )
    risk_rank = unique_profiles["risk_band"].map(risk_order).astype(float)
    if (
        composite.nunique() < MINIMUM_ASSOCIATION_LEVELS
        or risk_rank.nunique() < MINIMUM_ASSOCIATION_LEVELS
    ):
        raise ValueError("descriptive association must be finite")
    association = composite.rank(method="average").corr(risk_rank.rank(method="average"))

    risk_summary = (
        unique_profiles.groupby("risk_band", as_index=False, observed=True)
        .agg(
            unique_profiles=("profile_key", "count"),
            mean_exposure_score=("exposure_score", "mean"),
            mean_genetic_risk_score=("genetic_risk_score", "mean"),
            mean_obesity_score=("obesity_score", "mean"),
        )
        .assign(
            _order=lambda current: current["risk_band"].map(risk_order),
        )
        .sort_values("_order")
        .drop(columns="_order")
        .reset_index(drop=True)
    )
    score_columns = [
        "mean_exposure_score",
        "mean_genetic_risk_score",
        "mean_obesity_score",
    ]
    risk_summary[score_columns] = risk_summary[score_columns].round(2)

    duplicate_ledger = profile_counts.loc[profile_counts["record_count"] > 1].reset_index(
        drop=True
    )

    return AnalysisResult(
        lab_slug="cohort",
        grain="one unique fictional profile after duplicate audit",
        metrics={
            "source_record_count": len(evidence),
            "unique_profile_count": len(unique_profiles),
            "duplicate_record_count": int(len(evidence) - len(unique_profiles)),
            "descriptive_rank_association": _rounded(association),
        },
        primary_table=risk_summary,
        secondary_table=duplicate_ledger,
        notes=(
            "This is fictional synthetic data with no clinical validity.",
            "Risk bands are assigned independently from the analyzed score composite.",
            "This educational association does not imply causality, diagnose a "
            "person, or support medical action.",
        ),
    )


def analyze_restaurant_locations(frame: pd.DataFrame) -> AnalysisResult:
    """Partition accepted fictional coordinates from an explicit unresolved ledger."""

    validate_fixture(frame, RESTAURANT_CONTRACT)
    evidence = frame.copy(deep=True)
    latitude = pd.to_numeric(evidence["latitude"], errors="coerce")
    longitude = pd.to_numeric(evidence["longitude"], errors="coerce")
    accepted_mask = latitude.between(-90, 90) & longitude.between(-180, 180)

    accepted = evidence.loc[accepted_mask].copy()
    accepted["latitude"] = latitude.loc[accepted_mask]
    accepted["longitude"] = longitude.loc[accepted_mask]
    unresolved = evidence.loc[~accepted_mask].copy()
    unresolved["issue"] = "Coordinate is missing or outside geographic bounds"

    if not accepted.empty:
        validate_fixture(accepted, RESTAURANT_CONTRACT)

    return AnalysisResult(
        lab_slug="restaurant",
        grain="one fictional location record",
        metrics={
            "source_locations": len(evidence),
            "accepted_locations": len(accepted),
            "unresolved_locations": len(unresolved),
            "represented_regions": int(accepted["region"].nunique()),
        },
        primary_table=accepted.reset_index(drop=True),
        secondary_table=unresolved.reset_index(drop=True),
        notes=(
            "All location labels and geographic records are fictional.",
            "Unresolved coordinates remain in a visible ledger; none are invented.",
        ),
    )


def analyze_streaming_catalog(frame: pd.DataFrame) -> AnalysisResult:
    """Summarize fictional title duration by release period and genre."""

    validate_fixture(frame, STREAMING_CONTRACT)
    evidence = frame.copy(deep=True)
    evidence["release_period"] = evidence["release_year"].floordiv(10).mul(10).astype(str) + "s"

    catalog_summary = (
        evidence.groupby(
            ["release_period", "genre"],
            as_index=False,
            observed=True,
        )
        .agg(
            titles=("title_id", "count"),
            mean_duration_minutes=("duration_minutes", "mean"),
        )
        .sort_values(["release_period", "titles", "genre"], ascending=[True, False, True])
        .reset_index(drop=True)
    )
    catalog_summary["mean_duration_minutes"] = catalog_summary["mean_duration_minutes"].round(1)
    catalog_summary.insert(
        0,
        "catalog_slice",
        catalog_summary["release_period"] + " · " + catalog_summary["genre"],
    )

    type_summary = (
        evidence.groupby("content_type", as_index=False, observed=True)
        .agg(
            titles=("title_id", "count"),
            mean_duration_minutes=("duration_minutes", "mean"),
        )
        .sort_values("content_type")
        .reset_index(drop=True)
    )
    type_summary["mean_duration_minutes"] = type_summary["mean_duration_minutes"].round(1)

    return AnalysisResult(
        lab_slug="streaming",
        grain="one fictional catalog title",
        metrics={
            "source_titles": len(evidence),
            "genres": int(evidence["genre"].nunique()),
            "release_periods": int(evidence["release_period"].nunique()),
            "mean_duration_minutes": _rounded(
                evidence["duration_minutes"].mean(),
                1,
            ),
        },
        primary_table=catalog_summary,
        secondary_table=type_summary,
        notes=(
            "Every title identifier and catalog observation is fictional.",
            "Duration summaries are descriptive and preserve one-title grain.",
        ),
    )


def analyze_sports_outcomes(frame: pd.DataFrame) -> AnalysisResult:
    """Summarize fictional medals while preserving athlete-event grain."""

    validate_fixture(frame, SPORTS_CONTRACT)
    evidence = frame.copy(deep=True)

    team_summary = (
        evidence.groupby(["team", "continent"], as_index=False, observed=True)
        .agg(
            events=("event_id", "count"),
            athletes=("athlete_id", "nunique"),
            medals=("medal", "sum"),
            medal_rate=("medal", "mean"),
        )
        .sort_values(["medal_rate", "team"], ascending=[False, True])
        .reset_index(drop=True)
    )
    team_summary["medal_rate_percent"] = (team_summary.pop("medal_rate") * 100).round(1)

    weight_summary = (
        evidence.groupby("weight_class", as_index=False, observed=True)
        .agg(
            events=("event_id", "count"),
            medals=("medal", "sum"),
            medal_rate=("medal", "mean"),
        )
        .sort_values("weight_class")
        .reset_index(drop=True)
    )
    weight_summary["medal_rate_percent"] = (weight_summary.pop("medal_rate") * 100).round(1)

    return AnalysisResult(
        lab_slug="sports",
        grain="one fictional athlete-event",
        metrics={
            "source_events": len(evidence),
            "unique_athletes": int(evidence["athlete_id"].nunique()),
            "teams": int(evidence["team"].nunique()),
            "overall_medal_rate_percent": _rounded(
                evidence["medal"].mean() * 100,
                1,
            ),
        },
        primary_table=team_summary,
        secondary_table=weight_summary,
        notes=(
            "Teams, athlete identifiers, and event outcomes are fictional.",
            "Rates use athlete-events as the denominator and do not infer athlete skill.",
        ),
    )
