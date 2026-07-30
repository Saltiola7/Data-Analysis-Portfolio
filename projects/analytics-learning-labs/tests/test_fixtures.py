from __future__ import annotations

from collections.abc import Callable

import pandas as pd
import pytest

from analytics_learning_labs.fixtures import (
    generate_airline_fixture,
    generate_cohort_fixture,
    generate_restaurant_fixture,
    generate_sports_fixture,
    generate_streaming_fixture,
)

FixtureGenerator = Callable[..., pd.DataFrame]

FIXTURE_CASES: tuple[
    tuple[str, FixtureGenerator, int, str, tuple[str, ...]],
    ...,
] = (
    (
        "airline",
        generate_airline_fixture,
        160,
        "flight_id",
        (
            "flight_id",
            "carrier",
            "route",
            "arrival_delay_minutes",
            "carrier_delay_minutes",
            "late_aircraft_delay_minutes",
            "cancelled",
        ),
    ),
    (
        "cohort",
        generate_cohort_fixture,
        180,
        "record_id",
        (
            "record_id",
            "profile_key",
            "age_band",
            "exposure_score",
            "genetic_risk_score",
            "obesity_score",
            "risk_band",
        ),
    ),
    (
        "restaurant",
        generate_restaurant_fixture,
        140,
        "record_id",
        (
            "record_id",
            "location_label",
            "country",
            "region",
            "latitude",
            "longitude",
        ),
    ),
    (
        "streaming",
        generate_streaming_fixture,
        180,
        "title_id",
        (
            "title_id",
            "release_year",
            "duration_minutes",
            "genre",
            "content_type",
        ),
    ),
    (
        "sports",
        generate_sports_fixture,
        220,
        "event_id",
        (
            "event_id",
            "athlete_id",
            "team",
            "continent",
            "weight_class",
            "medal",
        ),
    ),
)

DEFAULT_FIXTURE_SHA256 = {
    "airline": "d8a745bbc8c53e973328fe0e83b2fcc9fc36b45cd70fbc0f6ee9f87ce157d6fb",
    "cohort": "5aa30097da9a8f47c9c2cb17e73c4bcd0d6938640de7e81d154d72e7cd83fdbc",
    "restaurant": "7e8ef86c9729ccc136698165234afbcf18ce5172077f2c0615642a02d6fe7e9e",
    "streaming": "223f9931a90bb95e1e65425c6f8998c345a723a01740609ce36ba5c292f18228",
    "sports": "4713eb2e3d93a9ecf7a2215cffcc7b665fa1c56d5d18d3cf3e7282b99db87977",
}


@pytest.mark.parametrize(
    ("slug", "generator", "default_rows", "grain_column", "required_columns"),
    FIXTURE_CASES,
)
def test_fixture_defaults_are_deterministic_and_match_declared_schema(
    slug: str,
    generator: FixtureGenerator,
    default_rows: int,
    grain_column: str,
    required_columns: tuple[str, ...],
) -> None:
    first = generator(seed=2026)
    second = generator(seed=2026)

    pd.testing.assert_frame_equal(first, second, check_exact=True)
    assert len(first) == default_rows
    assert tuple(first.columns) == required_columns
    assert first[grain_column].is_unique
    assert first[grain_column].notna().all()
    assert first[grain_column].astype(str).str.startswith(f"{slug}-").all()
    assert first.attrs["generator_version"]
    assert first.attrs["seed"] == 2026
    assert first.attrs["fixture_sha256"] == DEFAULT_FIXTURE_SHA256[slug]


@pytest.mark.parametrize(
    ("slug", "generator", "_default_rows", "_grain_column", "_required_columns"),
    FIXTURE_CASES,
)
def test_seed_changes_fixture_values(
    slug: str,
    generator: FixtureGenerator,
    _default_rows: int,
    _grain_column: str,
    _required_columns: tuple[str, ...],
) -> None:
    first = generator(seed=7, rows=20)
    second = generator(seed=8, rows=20)

    assert not first.equals(second), f"{slug} fixture ignored the seed"


@pytest.mark.parametrize(
    ("_slug", "generator", "_default_rows", "_grain_column", "_required_columns"),
    FIXTURE_CASES,
)
@pytest.mark.parametrize("rows", [0, 19, 10_000_000])
def test_fixture_generators_reject_unsupported_row_counts(
    _slug: str,
    generator: FixtureGenerator,
    _default_rows: int,
    _grain_column: str,
    _required_columns: tuple[str, ...],
    rows: int,
) -> None:
    with pytest.raises(ValueError):
        generator(seed=2026, rows=rows)


@pytest.mark.parametrize(
    ("_slug", "generator", "_default_rows", "_grain_column", "_required_columns"),
    FIXTURE_CASES,
)
@pytest.mark.parametrize("seed", [1.5, "2026", None])
def test_fixture_generators_require_an_integer_seed(
    _slug: str,
    generator: FixtureGenerator,
    _default_rows: int,
    _grain_column: str,
    _required_columns: tuple[str, ...],
    seed: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        generator(seed=seed, rows=20)  # type: ignore[arg-type]


def test_fixture_boundaries_and_synthetic_identifiers() -> None:
    airline = generate_airline_fixture(seed=2026, rows=40)
    cohort = generate_cohort_fixture(seed=2026, rows=40)
    restaurant = generate_restaurant_fixture(seed=2026, rows=40)
    streaming = generate_streaming_fixture(seed=2026, rows=40)
    sports = generate_sports_fixture(seed=2026, rows=40)

    assert (airline["carrier_delay_minutes"] >= 0).all()
    assert (airline["late_aircraft_delay_minutes"] >= 0).all()
    assert pd.api.types.is_bool_dtype(airline["cancelled"])
    cancelled_delay_columns = [
        "arrival_delay_minutes",
        "carrier_delay_minutes",
        "late_aircraft_delay_minutes",
    ]
    assert airline.loc[airline["cancelled"], cancelled_delay_columns].eq(0).all(axis=None)

    score_columns = ["exposure_score", "genetic_risk_score", "obesity_score"]
    assert cohort[score_columns].ge(0).all(axis=None)
    assert cohort[score_columns].le(10).all(axis=None)
    assert cohort["profile_key"].nunique() < len(cohort)

    resolved = restaurant[["latitude", "longitude"]].dropna()
    assert resolved["latitude"].between(-90, 90).all()
    assert resolved["longitude"].between(-180, 180).all()

    assert streaming["release_year"].between(1900, 2026).all()
    assert (streaming["duration_minutes"] > 0).all()

    assert pd.api.types.is_bool_dtype(sports["medal"])
    assert sports["athlete_id"].astype(str).str.startswith("athlete-").all()
    athlete_dimensions = sports.groupby("athlete_id")[
        ["team", "continent", "weight_class"]
    ].nunique()
    assert athlete_dimensions.eq(1).all(axis=None)
    assert sports.groupby("team")["continent"].nunique().eq(1).all()

    all_columns = {
        column.casefold()
        for frame in (airline, cohort, restaurant, streaming, sports)
        for column in frame.columns
    }
    assert not all_columns.intersection({"name", "email", "account_id", "employer", "person_id"})


def test_restaurant_default_fixture_exercises_unresolved_coordinate_path() -> None:
    frame = generate_restaurant_fixture(seed=2026, rows=40)

    unresolved = frame[["latitude", "longitude"]].isna().any(axis=1)

    assert unresolved.any()
    assert (~unresolved).any()


def test_cohort_risk_band_is_not_reconstructed_from_the_analyzed_score_mean() -> None:
    frame = generate_cohort_fixture(seed=2026, rows=60)
    composite = frame[["exposure_score", "genetic_risk_score", "obesity_score"]].mean(axis=1)
    reconstructed = pd.cut(
        composite,
        bins=[float("-inf"), 3.5, 6.5, float("inf")],
        labels=["low", "medium", "high"],
    ).astype(str)

    assert (reconstructed != frame["risk_band"]).any()
