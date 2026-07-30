from __future__ import annotations

from dataclasses import FrozenInstanceError

import pandas as pd
import pytest

from analytics_learning_labs.contracts import (
    AIRLINE_CONTRACT,
    COHORT_CONTRACT,
    RESTAURANT_CONTRACT,
    SPORTS_CONTRACT,
    AnalysisResult,
    FixtureContract,
    validate_fixture,
)


def _contract(
    slug: str,
    required_columns: tuple[str, ...],
    grain_columns: tuple[str, ...],
    *,
    maximum_rows: int = 2,
) -> FixtureContract:
    return FixtureContract(
        slug=slug,
        required_columns=required_columns,
        grain_columns=grain_columns,
        maximum_rows=maximum_rows,
    )


def test_contract_value_objects_are_frozen() -> None:
    fixture_contract = _contract("example", ("record_id",), ("record_id",))
    analysis_result = AnalysisResult(
        lab_slug="example",
        grain="one synthetic record",
        metrics={"rows": 1},
        primary_table=pd.DataFrame({"record_id": ["example-001"]}),
        secondary_table=None,
        notes=("Synthetic fixture.",),
    )

    with pytest.raises(FrozenInstanceError):
        fixture_contract.slug = "changed"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        analysis_result.lab_slug = "changed"  # type: ignore[misc]


def test_validate_fixture_accepts_a_complete_unique_frame() -> None:
    contract = _contract("example", ("record_id", "value"), ("record_id",))
    frame = pd.DataFrame(
        {
            "record_id": ["example-001", "example-002"],
            "value": [1, 2],
        }
    )

    assert validate_fixture(frame, contract) is None


@pytest.mark.parametrize(
    ("frame", "contract"),
    [
        (
            pd.DataFrame(columns=["record_id", "value"]),
            _contract("example", ("record_id", "value"), ("record_id",)),
        ),
        (
            pd.DataFrame({"record_id": ["example-001"]}),
            _contract("example", ("record_id", "value"), ("record_id",)),
        ),
        (
            pd.DataFrame(
                {
                    "record_id": ["example-001", "example-001"],
                    "value": [1, 2],
                }
            ),
            _contract("example", ("record_id", "value"), ("record_id",)),
        ),
        (
            pd.DataFrame(
                {
                    "record_id": ["example-001", None],
                    "value": [1, 2],
                }
            ),
            _contract("example", ("record_id", "value"), ("record_id",)),
        ),
        (
            pd.DataFrame(
                {
                    "record_id": [
                        "example-001",
                        "example-002",
                        "example-003",
                    ],
                    "value": [1, 2, 3],
                }
            ),
            _contract(
                "example",
                ("record_id", "value"),
                ("record_id",),
                maximum_rows=2,
            ),
        ),
    ],
    ids=[
        "empty",
        "missing-column",
        "duplicate-grain",
        "null-grain",
        "above-maximum",
    ],
)
def test_validate_fixture_rejects_structural_contract_violations(
    frame: pd.DataFrame,
    contract: FixtureContract,
) -> None:
    with pytest.raises(ValueError):
        validate_fixture(frame, contract)


def test_restaurant_contract_rejects_boolean_coordinates() -> None:
    frame = pd.DataFrame(
        {
            "record_id": ["restaurant-001"],
            "location_label": ["Location 001"],
            "country": ["Fictionland"],
            "region": ["North"],
            "latitude": [True],
            "longitude": [False],
        }
    )

    with pytest.raises(ValueError, match="numeric dtype"):
        validate_fixture(frame, RESTAURANT_CONTRACT)


def test_airline_contract_rejects_nonzero_cancelled_delay_placeholders() -> None:
    frame = pd.DataFrame(
        {
            "flight_id": ["airline-001"],
            "carrier": ["Demo Carrier Aster"],
            "route": ["Aster-Birch"],
            "arrival_delay_minutes": [10],
            "carrier_delay_minutes": [4],
            "late_aircraft_delay_minutes": [2],
            "cancelled": [True],
        }
    )

    with pytest.raises(ValueError, match="cancelled flights"):
        validate_fixture(frame, AIRLINE_CONTRACT)


def test_sports_contract_rejects_unstable_athlete_dimensions() -> None:
    frame = pd.DataFrame(
        {
            "event_id": ["sports-001", "sports-002"],
            "athlete_id": ["athlete-001", "athlete-001"],
            "team": ["Demo Team Aster", "Demo Team Cobalt"],
            "continent": ["Europe", "Asia"],
            "weight_class": ["Light", "Heavy"],
            "medal": [False, True],
        }
    )

    with pytest.raises(ValueError, match="athlete identity"):
        validate_fixture(frame, SPORTS_CONTRACT)


def test_cohort_contract_rejects_conflicting_duplicate_profiles() -> None:
    frame = pd.DataFrame(
        {
            "record_id": ["cohort-001", "cohort-002"],
            "profile_key": ["profile-001", "profile-001"],
            "age_band": ["40-49", "40-49"],
            "exposure_score": [1, 10],
            "genetic_risk_score": [4, 4],
            "obesity_score": [3, 3],
            "risk_band": ["low", "high"],
        }
    )

    with pytest.raises(ValueError, match="duplicate profile"):
        validate_fixture(frame, COHORT_CONTRACT)


def test_cohort_contract_treats_risk_band_case_as_equivalent() -> None:
    frame = pd.DataFrame(
        {
            "record_id": ["cohort-001", "cohort-002"],
            "profile_key": ["profile-001", "profile-001"],
            "age_band": ["40-49", "40-49"],
            "exposure_score": [1, 1],
            "genetic_risk_score": [4, 4],
            "obesity_score": [3, 3],
            "risk_band": ["LOW", "low"],
        }
    )

    assert validate_fixture(frame, COHORT_CONTRACT) is None


@pytest.mark.parametrize(
    ("slug", "frame", "required_columns", "grain_columns"),
    [
        (
            "airline",
            pd.DataFrame(
                {
                    "flight_id": ["airline-001"],
                    "carrier": ["Northwind Air"],
                    "route": ["AAA-BBB"],
                    "arrival_delay_minutes": [5],
                    "carrier_delay_minutes": [-1],
                    "late_aircraft_delay_minutes": [0],
                    "cancelled": [False],
                }
            ),
            (
                "flight_id",
                "carrier",
                "route",
                "arrival_delay_minutes",
                "carrier_delay_minutes",
                "late_aircraft_delay_minutes",
                "cancelled",
            ),
            ("flight_id",),
        ),
        (
            "cohort",
            pd.DataFrame(
                {
                    "record_id": ["cohort-001"],
                    "profile_key": ["profile-001"],
                    "age_band": ["40-49"],
                    "exposure_score": [11],
                    "genetic_risk_score": [4],
                    "obesity_score": [3],
                    "risk_band": ["medium"],
                }
            ),
            (
                "record_id",
                "profile_key",
                "age_band",
                "exposure_score",
                "genetic_risk_score",
                "obesity_score",
                "risk_band",
            ),
            ("record_id",),
        ),
        (
            "streaming",
            pd.DataFrame(
                {
                    "title_id": ["streaming-001"],
                    "release_year": [1800],
                    "duration_minutes": [0],
                    "genre": ["Documentary"],
                    "content_type": ["Film"],
                }
            ),
            (
                "title_id",
                "release_year",
                "duration_minutes",
                "genre",
                "content_type",
            ),
            ("title_id",),
        ),
        (
            "sports",
            pd.DataFrame(
                {
                    "event_id": ["sports-001"],
                    "athlete_id": ["athlete-001"],
                    "team": ["Team North"],
                    "continent": ["Europe"],
                    "weight_class": ["Light"],
                    "medal": ["yes"],
                }
            ),
            (
                "event_id",
                "athlete_id",
                "team",
                "continent",
                "weight_class",
                "medal",
            ),
            ("event_id",),
        ),
    ],
)
def test_validate_fixture_rejects_lab_boundary_violations(
    slug: str,
    frame: pd.DataFrame,
    required_columns: tuple[str, ...],
    grain_columns: tuple[str, ...],
) -> None:
    contract = _contract(slug, required_columns, grain_columns)

    with pytest.raises(ValueError):
        validate_fixture(frame, contract)


def test_validate_fixture_rejects_numeric_strings_before_analysis() -> None:
    frame = pd.DataFrame(
        {
            "flight_id": ["airline-001"],
            "carrier": ["Northwind Air"],
            "route": ["AAA-BBB"],
            "arrival_delay_minutes": ["5"],
            "carrier_delay_minutes": ["1"],
            "late_aircraft_delay_minutes": ["0"],
            "cancelled": [False],
        }
    )
    contract = _contract(
        "airline",
        (
            "flight_id",
            "carrier",
            "route",
            "arrival_delay_minutes",
            "carrier_delay_minutes",
            "late_aircraft_delay_minutes",
            "cancelled",
        ),
        ("flight_id",),
    )

    with pytest.raises(ValueError, match="numeric dtype"):
        validate_fixture(frame, contract)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("carrier", None),
        ("route", " "),
    ],
)
def test_validate_fixture_rejects_missing_or_blank_analytical_dimensions(
    column: str,
    value: object,
) -> None:
    frame = pd.DataFrame(
        {
            "flight_id": ["airline-001"],
            "carrier": ["Northwind Air"],
            "route": ["AAA-BBB"],
            "arrival_delay_minutes": [5],
            "carrier_delay_minutes": [1],
            "late_aircraft_delay_minutes": [0],
            "cancelled": [False],
        }
    )
    frame.loc[0, column] = value
    contract = _contract(
        "airline",
        tuple(frame.columns),
        ("flight_id",),
    )

    with pytest.raises(ValueError, match="analytical dimension"):
        validate_fixture(frame, contract)


def test_validate_fixture_rejects_nullable_boolean_values() -> None:
    frame = pd.DataFrame(
        {
            "flight_id": ["airline-001"],
            "carrier": ["Northwind Air"],
            "route": ["AAA-BBB"],
            "arrival_delay_minutes": [5],
            "carrier_delay_minutes": [1],
            "late_aircraft_delay_minutes": [0],
            "cancelled": pd.Series([pd.NA], dtype="boolean"),
        }
    )
    contract = _contract(
        "airline",
        tuple(frame.columns),
        ("flight_id",),
    )

    with pytest.raises(ValueError, match="boolean"):
        validate_fixture(frame, contract)
