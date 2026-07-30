from __future__ import annotations

import json
import math
from collections.abc import Callable

import pandas as pd
import pytest

from analytics_learning_labs.analysis import (
    analyze_airline_delays,
    analyze_restaurant_locations,
    analyze_sports_outcomes,
    analyze_streaming_catalog,
    analyze_synthetic_cohort,
)
from analytics_learning_labs.contracts import AnalysisResult
from analytics_learning_labs.fixtures import (
    generate_airline_fixture,
    generate_cohort_fixture,
    generate_restaurant_fixture,
    generate_sports_fixture,
    generate_streaming_fixture,
)

FixtureGenerator = Callable[..., pd.DataFrame]
Analyzer = Callable[[pd.DataFrame], AnalysisResult]

ANALYSIS_CASES: tuple[
    tuple[str, FixtureGenerator, Analyzer, str],
    ...,
] = (
    (
        "airline",
        generate_airline_fixture,
        analyze_airline_delays,
        "flight",
    ),
    (
        "cohort",
        generate_cohort_fixture,
        analyze_synthetic_cohort,
        "profile",
    ),
    (
        "restaurant",
        generate_restaurant_fixture,
        analyze_restaurant_locations,
        "location",
    ),
    (
        "streaming",
        generate_streaming_fixture,
        analyze_streaming_catalog,
        "title",
    ),
    (
        "sports",
        generate_sports_fixture,
        analyze_sports_outcomes,
        "event",
    ),
)


def _metric_with_tokens(
    result: AnalysisResult,
    *,
    required: tuple[str, ...],
    alternatives: tuple[str, ...] = (),
) -> int | float | str:
    for key, value in result.metrics.items():
        normalized = key.casefold()
        if all(token in normalized for token in required) and (
            not alternatives or any(token in normalized for token in alternatives)
        ):
            return value
    pytest.fail(
        f"No metric key contains {required!r}"
        + (f" and one of {alternatives!r}" if alternatives else "")
    )


@pytest.mark.parametrize(
    ("slug", "generator", "analyzer", "grain_token"),
    ANALYSIS_CASES,
)
def test_analyses_return_finite_json_compatible_evidence(
    slug: str,
    generator: FixtureGenerator,
    analyzer: Analyzer,
    grain_token: str,
) -> None:
    frame = generator(seed=2026, rows=40)

    result = analyzer(frame)

    assert isinstance(result, AnalysisResult)
    assert result.lab_slug == slug
    assert grain_token in result.grain.casefold()
    assert isinstance(result.primary_table, pd.DataFrame)
    assert not result.primary_table.empty
    assert isinstance(result.notes, tuple)
    assert result.notes
    json.dumps(dict(result.metrics), allow_nan=False)
    for value in result.metrics.values():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            assert math.isfinite(value)


@pytest.mark.parametrize(
    ("_slug", "generator", "analyzer", "_grain_token"),
    ANALYSIS_CASES,
)
def test_analyses_fail_closed_on_missing_required_columns(
    _slug: str,
    generator: FixtureGenerator,
    analyzer: Analyzer,
    _grain_token: str,
) -> None:
    frame = generator(seed=2026, rows=20)
    invalid = frame.drop(columns=[frame.columns[0]])

    with pytest.raises(ValueError):
        analyzer(invalid)


def test_airline_delay_means_use_completed_flights_only() -> None:
    frame = pd.DataFrame(
        {
            "flight_id": ["airline-001", "airline-002"],
            "carrier": ["Demo Carrier Aster", "Demo Carrier Aster"],
            "route": ["Aster-Birch", "Aster-Birch"],
            "arrival_delay_minutes": [10, 0],
            "carrier_delay_minutes": [4, 0],
            "late_aircraft_delay_minutes": [2, 0],
            "cancelled": [False, True],
        }
    )

    result = analyze_airline_delays(frame)
    carrier = result.primary_table.iloc[0]

    assert carrier["flights"] == 2
    assert carrier["completed_flights"] == 1
    assert carrier["cancelled_flights"] == 1
    assert carrier["mean_arrival_delay_minutes"] == 10
    assert carrier["mean_carrier_delay_minutes"] == 4
    assert carrier["mean_late_aircraft_delay_minutes"] == 2


def test_cohort_analysis_names_source_and_unique_profile_denominators() -> None:
    frame = generate_cohort_fixture(seed=2026, rows=60)

    result = analyze_synthetic_cohort(frame)

    source_records = _metric_with_tokens(
        result,
        required=("source",),
        alternatives=("record", "row"),
    )
    unique_profiles = _metric_with_tokens(
        result,
        required=("unique", "profile"),
    )
    assert source_records == len(frame)
    assert unique_profiles == frame["profile_key"].nunique()

    safety_copy = " ".join(result.notes).casefold()
    assert "fictional" in safety_copy
    assert "clinical" in safety_copy
    assert "association" in safety_copy or "descriptive" in safety_copy
    assert (
        "no causal" in safety_copy
        or "not causal" in safety_copy
        or "does not imply caus" in safety_copy
    )


def test_cohort_analysis_rejects_a_non_finite_association() -> None:
    frame = generate_cohort_fixture(seed=2026, rows=40)
    frame["risk_band"] = "low"

    with pytest.raises(ValueError, match="finite"):
        analyze_synthetic_cohort(frame)


def test_cohort_analysis_normalizes_valid_risk_band_case() -> None:
    frame = generate_cohort_fixture(seed=2026, rows=60)
    frame["risk_band"] = frame["risk_band"].str.upper()

    result = analyze_synthetic_cohort(frame)

    assert set(result.primary_table["risk_band"]) == {"low", "medium", "high"}


def test_restaurant_analysis_retains_unresolved_coordinates_in_a_ledger() -> None:
    frame = generate_restaurant_fixture(seed=2026, rows=20)
    unresolved_id = frame.loc[0, "record_id"]
    frame.loc[0, ["latitude", "longitude"]] = [None, None]

    result = analyze_restaurant_locations(frame)

    assert result.secondary_table is not None
    assert unresolved_id in set(result.secondary_table["record_id"])
    accepted_ids = set(result.primary_table["record_id"])
    unresolved_ids = set(result.secondary_table["record_id"])
    assert accepted_ids.isdisjoint(unresolved_ids)
    assert accepted_ids | unresolved_ids == set(frame["record_id"])


def test_restaurant_analysis_rejects_out_of_range_coordinates() -> None:
    frame = generate_restaurant_fixture(seed=2026, rows=20)
    frame.loc[1, "latitude"] = 999.0

    with pytest.raises(ValueError, match="latitude"):
        analyze_restaurant_locations(frame)


def test_restaurant_analysis_rejects_nonfinite_coordinate_beside_a_null() -> None:
    frame = generate_restaurant_fixture(seed=2026, rows=20)
    frame.loc[1, ["latitude", "longitude"]] = [float("inf"), None]

    with pytest.raises(ValueError, match="finite"):
        analyze_restaurant_locations(frame)


def test_airline_summary_exposes_both_delay_components() -> None:
    result = analyze_airline_delays(generate_airline_fixture(seed=2026, rows=40))

    assert {
        "mean_carrier_delay_minutes",
        "mean_late_aircraft_delay_minutes",
    }.issubset(result.primary_table.columns)


def test_streaming_summary_has_unambiguous_catalog_slice_labels() -> None:
    result = analyze_streaming_catalog(generate_streaming_fixture(seed=2026, rows=40))

    assert "catalog_slice" in result.primary_table.columns
    assert result.primary_table["catalog_slice"].is_unique
