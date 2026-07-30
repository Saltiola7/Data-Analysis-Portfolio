from __future__ import annotations

import copy
import json

import pandas as pd
import pytest

from wellness_data_pipeline import (
    NormalizationError,
    SchemaError,
    audit_to_json,
    dataframe_to_safe_csv,
    normalize_dose_mg,
    normalize_duration,
    run_pipeline,
)


def valid_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    participants = pd.DataFrame(
        [
            {"participant_id": "P-001", "cohort": "alpha", "joined_on": "2026-01-01"},
            {"participant_id": "P-002", "cohort": "beta", "joined_on": "2026-01-01"},
        ]
    )
    daily_signals = pd.DataFrame(
        [
            {
                "participant_id": "P-001",
                "observed_on": "2026-01-02",
                "sleep_value": 8,
                "sleep_unit": "hours",
                "active_value": 45,
                "active_unit": "min",
                "pulse_bpm": 64,
            },
            {
                "participant_id": "P-002",
                "observed_on": "2026-01-02",
                "sleep_value": 420,
                "sleep_unit": "minutes",
                "active_value": 1.25,
                "active_unit": "h",
                "pulse_bpm": 70,
            },
        ]
    )
    interventions = pd.DataFrame(
        [
            {
                "intervention_id": "I-001",
                "participant_id": "P-001",
                "occurred_on": "2026-01-02",
                "intervention": "routine-a",
                "dose_value": 500,
                "dose_unit": "mcg",
            },
            {
                "intervention_id": "I-002",
                "participant_id": "P-001",
                "occurred_on": "2026-01-02",
                "intervention": "routine-b",
                "dose_value": 0.002,
                "dose_unit": "g",
            },
        ]
    )
    return participants, daily_signals, interventions


@pytest.mark.parametrize(
    ("value", "unit", "expected"),
    [
        (30, "minute", 30.0),
        (30, "minutes", 30.0),
        (30, "min", 30.0),
        (1.25, "hour", 75.0),
        (1.25, "hours", 75.0),
        (1.25, "h", 75.0),
    ],
)
def test_normalize_duration_supported_units(value: float, unit: str, expected: float) -> None:
    assert normalize_duration(value, unit) == expected


@pytest.mark.parametrize(
    ("value", "unit", "expected"),
    [
        (250, "mcg", 0.25),
        (250, "ug", 0.25),
        (2.5, "mg", 2.5),
        (0.125, "g", 125.0),
    ],
)
def test_normalize_dose_supported_units(value: float, unit: str, expected: float) -> None:
    assert normalize_dose_mg(value, unit) == expected


@pytest.mark.parametrize(
    ("function", "value", "unit"),
    [
        (normalize_duration, 1, "day"),
        (normalize_duration, 1, None),
        (normalize_dose_mg, 1, "ounce"),
        (normalize_dose_mg, 1, ""),
    ],
)
def test_normalizers_reject_unsupported_or_missing_units(
    function: object, value: float, unit: object
) -> None:
    with pytest.raises(NormalizationError, match="unsupported"):
        function(value, unit)  # type: ignore[operator]


def test_missing_required_fields_fail_before_row_processing() -> None:
    participants, daily_signals, interventions = valid_inputs()
    participants = participants.drop(columns=["cohort"])

    with pytest.raises(SchemaError, match=r"participants.*cohort"):
        run_pipeline(participants, daily_signals, interventions)


def test_input_row_limit_fails_before_row_processing() -> None:
    participants, daily_signals, interventions = valid_inputs()
    oversized = pd.concat([daily_signals.iloc[[0]]] * 10_001, ignore_index=True)

    with pytest.raises(SchemaError, match=r"daily_signals.*10,000"):
        run_pipeline(participants, oversized, interventions)


def test_multiple_interventions_do_not_multiply_participant_day_grain() -> None:
    participants, daily_signals, interventions = valid_inputs()

    result = run_pipeline(participants, daily_signals, interventions)

    assert list(result.participant_days["participant_id"]) == ["P-001", "P-002"]
    first_day = result.participant_days.iloc[0]
    assert first_day["sleep_minutes"] == 480.0
    assert first_day["active_minutes"] == 45.0
    assert first_day["average_pulse_bpm"] == 64.0
    assert first_day["intervention_event_count"] == 2
    assert first_day["total_intervention_dose_mg"] == 2.5
    assert result.participant_days.duplicated(["participant_id", "observed_on"]).sum() == 0


def test_every_conflicting_daily_signal_row_is_rejected() -> None:
    participants, daily_signals, interventions = valid_inputs()
    conflict = daily_signals.iloc[[0]].copy()
    conflict["sleep_value"] = 7
    daily_signals = pd.concat([daily_signals, conflict], ignore_index=True)

    result = run_pipeline(participants, daily_signals, interventions)

    duplicate_rejections = result.rejected_records.query(
        "source == 'daily_signals' and reason_code == 'duplicate_signal_key'"
    )
    assert len(duplicate_rejections) == 2
    assert list(result.participant_days["participant_id"]) == ["P-002"]
    assert result.audit["duplicate_counts"]["daily_signals"] == 2


def test_duplicate_participants_and_interventions_have_no_arbitrary_winner() -> None:
    participants, daily_signals, interventions = valid_inputs()
    participants = pd.concat([participants, participants.iloc[[0]]], ignore_index=True)
    interventions = pd.concat([interventions, interventions.iloc[[0]]], ignore_index=True)

    result = run_pipeline(participants, daily_signals, interventions)

    rejected = result.rejected_records
    assert (
        len(
            rejected.query(
                "source == 'participants' and reason_code == 'duplicate_participant_id'"
            )
        )
        == 2
    )
    assert (
        len(
            rejected.query(
                "source == 'interventions' and reason_code == 'duplicate_intervention_id'"
            )
        )
        == 2
    )
    assert (
        len(rejected.query("source == 'daily_signals' and reason_code == 'unknown_participant'"))
        == 1
    )
    assert result.audit["duplicate_counts"] == {
        "participants": 2,
        "daily_signals": 0,
        "interventions": 2,
    }


def test_invalid_values_units_dates_and_unknown_participants_are_rejected() -> None:
    participants, daily_signals, interventions = valid_inputs()
    daily_signals = pd.concat(
        [
            daily_signals,
            pd.DataFrame(
                [
                    {
                        "participant_id": "P-001",
                        "observed_on": "2026-01-03",
                        "sleep_value": -1,
                        "sleep_unit": "h",
                        "active_value": 20,
                        "active_unit": "min",
                        "pulse_bpm": 60,
                    },
                    {
                        "participant_id": "P-001",
                        "observed_on": "2026-01-04",
                        "sleep_value": 8,
                        "sleep_unit": "days",
                        "active_value": 20,
                        "active_unit": "min",
                        "pulse_bpm": 60,
                    },
                    {
                        "participant_id": "P-404",
                        "observed_on": "2026-01-05",
                        "sleep_value": 8,
                        "sleep_unit": "h",
                        "active_value": 20,
                        "active_unit": "min",
                        "pulse_bpm": 60,
                    },
                    {
                        "participant_id": "P-002",
                        "observed_on": "01/06/2026",
                        "sleep_value": 8,
                        "sleep_unit": "h",
                        "active_value": 20,
                        "active_unit": "min",
                        "pulse_bpm": 60,
                    },
                ]
            ),
        ],
        ignore_index=True,
    )
    interventions = pd.concat(
        [
            interventions,
            pd.DataFrame(
                [
                    {
                        "intervention_id": "I-003",
                        "participant_id": "P-404",
                        "occurred_on": "2026-01-02",
                        "intervention": "routine-c",
                        "dose_value": 1,
                        "dose_unit": "mg",
                    },
                    {
                        "intervention_id": "I-004",
                        "participant_id": "P-002",
                        "occurred_on": "2026-01-02",
                        "intervention": "routine-c",
                        "dose_value": -1,
                        "dose_unit": "mg",
                    },
                ]
            ),
        ],
        ignore_index=True,
    )

    result = run_pipeline(participants, daily_signals, interventions)

    reason_codes = set(result.rejected_records["reason_code"])
    assert {
        "negative_value",
        "unsupported_duration_unit",
        "unknown_participant",
        "invalid_date",
    }.issubset(reason_codes)
    assert result.audit["missing_participant_counts"] == {
        "daily_signals": 1,
        "interventions": 1,
    }


def test_pipeline_is_idempotent_and_does_not_mutate_inputs() -> None:
    participants, daily_signals, interventions = valid_inputs()
    originals = tuple(
        copy.deepcopy(frame) for frame in (participants, daily_signals, interventions)
    )

    first = run_pipeline(participants, daily_signals, interventions)
    second = run_pipeline(participants, daily_signals, interventions)

    pd.testing.assert_frame_equal(first.participant_days, second.participant_days)
    pd.testing.assert_frame_equal(first.rejected_records, second.rejected_records)
    assert first.audit == second.audit
    for frame, original in zip(
        (participants, daily_signals, interventions), originals, strict=True
    ):
        pd.testing.assert_frame_equal(frame, original)


def test_audit_balances_sources_and_serializes_canonically() -> None:
    participants, daily_signals, interventions = valid_inputs()

    result = run_pipeline(participants, daily_signals, interventions)
    audit = result.audit

    for source in ("participants", "daily_signals", "interventions"):
        assert audit["source_counts"][source] == (
            audit["accepted_counts"][source] + audit["rejected_counts"][source]
        )
    assert audit["output_count"] == len(result.participant_days)
    assert all(len(value) == 64 for value in audit["content_hashes"].values())
    assert audit_to_json(result) == json.dumps(
        audit, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )


def test_safe_csv_escapes_spreadsheet_formula_prefixes_without_changing_numbers() -> None:
    frame = pd.DataFrame(
        {
            "text": ["=SUM(A1:A2)", "+cmd", "-cmd", "@lookup", "\tformula", "\rformula", "safe"],
            "number": [-4, 2, 0, 1, 5, 6, 7],
        }
    )

    exported = pd.read_csv(pd.io.common.StringIO(dataframe_to_safe_csv(frame)))

    assert list(exported["text"]) == [
        "'=SUM(A1:A2)",
        "'+cmd",
        "'-cmd",
        "'@lookup",
        "'\tformula",
        "'\rformula",
        "safe",
    ]
    assert list(exported["number"]) == [-4, 2, 0, 1, 5, 6, 7]
