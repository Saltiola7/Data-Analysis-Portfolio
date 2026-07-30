"""Deterministic, fictional fixture generators for the learning labs."""

from __future__ import annotations

import hashlib
import random
from collections.abc import Callable

import pandas as pd

from analytics_learning_labs.contracts import (
    AIRLINE_CONTRACT,
    COHORT_CONTRACT,
    RESTAURANT_CONTRACT,
    SPORTS_CONTRACT,
    STREAMING_CONTRACT,
    FixtureContract,
    validate_fixture,
)

GENERATOR_VERSION = "analytics-learning-labs/1.0"
MINIMUM_FIXTURE_ROWS = 20
AIRLINE_CANCELLATION_RATE = 0.06
CARRIER_DELAY_ZERO_RATE = 0.58
LATE_AIRCRAFT_DELAY_ZERO_RATE = 0.66
MEDAL_RATE = 0.29
RISK_BANDS = ("low", "medium", "high")
MISSING_LATITUDE_INTERVAL = 13
MISSING_LONGITUDE_INTERVAL = 17


def _validate_generation_request(
    seed: int,
    rows: int,
    contract: FixtureContract,
) -> random.Random:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer")
    if isinstance(rows, bool) or not isinstance(rows, int):
        raise TypeError("rows must be an integer")
    if not MINIMUM_FIXTURE_ROWS <= rows <= contract.maximum_rows:
        raise ValueError(
            f"rows must be between {MINIMUM_FIXTURE_ROWS} and {contract.maximum_rows}"
        )
    return random.Random(seed)


def _finalize_fixture(
    frame: pd.DataFrame,
    *,
    seed: int,
    contract: FixtureContract,
) -> pd.DataFrame:
    frame = frame.loc[:, list(contract.required_columns)]
    frame.attrs["generator_version"] = GENERATOR_VERSION
    frame.attrs["seed"] = seed
    validate_fixture(frame, contract)
    serialized = frame.to_csv(
        index=False,
        lineterminator="\n",
        float_format="%.17g",
    )
    frame.attrs["fixture_sha256"] = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return frame


def generate_airline_fixture(seed: int, rows: int = 160) -> pd.DataFrame:
    """Generate fictional flight events at one row per flight."""

    rng = _validate_generation_request(seed, rows, AIRLINE_CONTRACT)
    carriers = (
        "Demo Carrier Aster",
        "Demo Carrier Birch",
        "Demo Carrier Cobalt",
        "Demo Carrier Dune",
    )
    routes = (
        "Aster-Birch",
        "Aster-Cobalt",
        "Birch-Dune",
        "Cobalt-Ember",
        "Dune-Fjord",
    )
    records: list[dict[str, object]] = []
    for index in range(rows):
        cancelled = rng.random() < AIRLINE_CANCELLATION_RATE
        carrier_delay = (
            0 if cancelled or rng.random() < CARRIER_DELAY_ZERO_RATE else rng.randint(1, 55)
        )
        late_aircraft_delay = (
            0 if cancelled or rng.random() < LATE_AIRCRAFT_DELAY_ZERO_RATE else rng.randint(1, 70)
        )
        base_delay = 0 if cancelled else rng.randint(-18, 24)
        records.append(
            {
                "flight_id": f"airline-{seed}-{index + 1:04d}",
                "carrier": rng.choice(carriers),
                "route": rng.choice(routes),
                "arrival_delay_minutes": base_delay + carrier_delay + late_aircraft_delay,
                "carrier_delay_minutes": carrier_delay,
                "late_aircraft_delay_minutes": late_aircraft_delay,
                "cancelled": cancelled,
            }
        )

    return _finalize_fixture(
        pd.DataFrame.from_records(records),
        seed=seed,
        contract=AIRLINE_CONTRACT,
    )


def generate_cohort_fixture(seed: int, rows: int = 180) -> pd.DataFrame:
    """Generate fictional profile observations with deliberate duplicate profiles."""

    rng = _validate_generation_request(seed, rows, COHORT_CONTRACT)
    profile_count = max(MINIMUM_FIXTURE_ROWS, int(rows * 0.75))
    age_bands = ("20-29", "30-39", "40-49", "50-59", "60-69")
    profiles: list[dict[str, object]] = []
    for index in range(profile_count):
        exposure = rng.randint(0, 10)
        genetic = rng.randint(0, 10)
        obesity = rng.randint(0, 10)
        risk_band = RISK_BANDS[index] if index < len(RISK_BANDS) else rng.choice(RISK_BANDS)
        profiles.append(
            {
                "profile_key": f"profile-{seed}-{index + 1:04d}",
                "age_band": rng.choice(age_bands),
                "exposure_score": exposure,
                "genetic_risk_score": genetic,
                "obesity_score": obesity,
                "risk_band": risk_band,
            }
        )

    records: list[dict[str, object]] = []
    for index in range(rows):
        profile = profiles[index % profile_count]
        records.append(
            {
                "record_id": f"cohort-{seed}-{index + 1:04d}",
                **profile,
            }
        )

    return _finalize_fixture(
        pd.DataFrame.from_records(records),
        seed=seed,
        contract=COHORT_CONTRACT,
    )


def generate_restaurant_fixture(seed: int, rows: int = 140) -> pd.DataFrame:
    """Generate fictional locations with bounded missing-coordinate examples."""

    rng = _validate_generation_request(seed, rows, RESTAURANT_CONTRACT)
    locations = (
        ("Fictionland", "North", 48.0, 12.0),
        ("Fictionland", "South", 18.0, 24.0),
        ("Example Republic", "Coast", 36.0, -8.0),
        ("Example Republic", "Highlands", 52.0, -2.0),
        ("Demo Isles", "Central", -22.0, 142.0),
    )
    records: list[dict[str, object]] = []
    for index in range(rows):
        country, region, latitude_center, longitude_center = rng.choice(locations)
        latitude: float | None = round(
            latitude_center + rng.uniform(-4.5, 4.5),
            4,
        )
        longitude: float | None = round(
            longitude_center + rng.uniform(-6.0, 6.0),
            4,
        )
        if index % MISSING_LATITUDE_INTERVAL == 0:
            latitude = None
        elif index % MISSING_LONGITUDE_INTERVAL == 0:
            longitude = None
        records.append(
            {
                "record_id": f"restaurant-{seed}-{index + 1:04d}",
                "location_label": f"Location {index + 1:03d}",
                "country": country,
                "region": region,
                "latitude": latitude,
                "longitude": longitude,
            }
        )

    return _finalize_fixture(
        pd.DataFrame.from_records(records),
        seed=seed,
        contract=RESTAURANT_CONTRACT,
    )


def generate_streaming_fixture(seed: int, rows: int = 180) -> pd.DataFrame:
    """Generate fictional catalog-title observations."""

    rng = _validate_generation_request(seed, rows, STREAMING_CONTRACT)
    genres = ("Animation", "Comedy", "Documentary", "Drama", "Science Fiction")
    content_types = ("Film", "Special")
    records = [
        {
            "title_id": f"streaming-{seed}-{index + 1:04d}",
            "release_year": rng.randint(1980, 2026),
            "duration_minutes": rng.randint(42, 185),
            "genre": rng.choice(genres),
            "content_type": rng.choice(content_types),
        }
        for index in range(rows)
    ]

    return _finalize_fixture(
        pd.DataFrame.from_records(records),
        seed=seed,
        contract=STREAMING_CONTRACT,
    )


def generate_sports_fixture(seed: int, rows: int = 220) -> pd.DataFrame:
    """Generate fictional athlete-event observations without person names."""

    rng = _validate_generation_request(seed, rows, SPORTS_CONTRACT)
    teams = (
        ("Demo Team Aster", "Europe"),
        ("Demo Team Birch", "North America"),
        ("Demo Team Cobalt", "Asia"),
        ("Demo Team Dune", "Europe"),
        ("Demo Team Ember", "South America"),
    )
    weight_classes = ("Light", "Middle", "Heavy")
    athlete_count = max(MINIMUM_FIXTURE_ROWS, int(rows * 0.7))
    athlete_profiles = [
        (*rng.choice(teams), rng.choice(weight_classes)) for _ in range(athlete_count)
    ]
    records: list[dict[str, object]] = []
    for index in range(rows):
        team, continent, weight_class = athlete_profiles[index % athlete_count]
        records.append(
            {
                "event_id": f"sports-{seed}-{index + 1:04d}",
                "athlete_id": f"athlete-{seed}-{index % athlete_count + 1:04d}",
                "team": team,
                "continent": continent,
                "weight_class": weight_class,
                "medal": rng.random() < MEDAL_RATE,
            }
        )

    return _finalize_fixture(
        pd.DataFrame.from_records(records),
        seed=seed,
        contract=SPORTS_CONTRACT,
    )


FixtureGenerator = Callable[[int, int], pd.DataFrame]
