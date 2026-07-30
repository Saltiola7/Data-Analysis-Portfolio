from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from public_sector_opportunity_pipeline import (
    MAX_SOURCE_RECORDS,
    PipelineInputError,
    PipelineState,
    generate_synthetic_sources,
    run_pipeline,
)
from public_sector_opportunity_pipeline.hashing import content_hash


def federal_record(
    *,
    source_id: str | None = "FED-001",
    title: str = "Cloud data modernization",
    published: str = "2026-07-01",
    closes: str = "2026-08-01",
    engagement: str = "task_order",
    minimum: object = 100_000,
    maximum: object = 250_000,
    updated: str = "2026-07-01T12:00:00Z",
) -> dict[str, object]:
    return {
        "notice_id": source_id,
        "notice_title": title,
        "bureau": "Digital Services Office",
        "published_on": published,
        "closes_on": closes,
        "work_location": "remote",
        "award_type": engagement,
        "min_value_usd": minimum,
        "max_value_usd": maximum,
        "capabilities": ["Python", "GCP", "Data Engineering"],
        "modified_at": updated,
    }


def municipal_record(
    *,
    source_id: str | None = "MUN-001",
    title: str = "Analytics platform implementation",
    published: str = "2026-07-03",
    closes: str = "2026-08-15",
    engagement: str = "project",
    minimum: object = 80_000,
    maximum: object = 180_000,
    updated: str = "2026-07-03T09:30:00-05:00",
) -> dict[str, object]:
    return {
        "solicitation_number": source_id,
        "name": title,
        "department": "City Innovation Lab",
        "posted_at": published,
        "deadline": closes,
        "remote_policy": "hybrid",
        "engagement_model": engagement,
        "budget_floor": minimum,
        "budget_ceiling": maximum,
        "required_skills": "analytics|sql|python",
        "updated_at": updated,
    }


def test_synthetic_fixture_is_deterministic_and_versioned() -> None:
    first = generate_synthetic_sources(seed=2026)
    second = generate_synthetic_sources(seed=2026)

    assert first == second
    assert first.version == "synthetic-v1"
    assert tuple(sorted(first.batches)) == ("federal", "municipal")
    assert sum(len(batch) for batch in first.batches.values()) > 0


def test_two_source_schemas_normalize_to_one_canonical_grain() -> None:
    result = run_pipeline(
        {
            "federal": [federal_record()],
            "municipal": [municipal_record()],
        }
    )

    assert result.opportunities["canonical_id"].tolist() == [
        "federal:FED-001",
        "municipal:MUN-001",
    ]
    assert result.opportunities["engagement_type"].tolist() == [
        "contract",
        "project",
    ]
    assert result.opportunities["skill_tags"].tolist() == [
        "data-engineering|gcp|python",
        "analytics|python|sql",
    ]
    assert result.rejected.empty
    assert result.manifest.output_grain == "one row per source and source_id"
    assert result.manifest.input_count == 2
    assert result.manifest.accepted_count == 2


@pytest.mark.parametrize(
    ("record", "reason"),
    [
        (federal_record(source_id=None), "missing_identity"),
        (federal_record(published="07/01/2026"), "invalid_date"),
        (
            federal_record(published="2026-08-02", closes="2026-08-01"),
            "inverted_closing_window",
        ),
        (federal_record(engagement="employment"), "unsupported_engagement"),
        (federal_record(minimum=-1), "invalid_value"),
        (federal_record(minimum=300_000, maximum=250_000), "invalid_value_band"),
        (federal_record(updated="2026-07-01 12:00"), "invalid_update_timestamp"),
    ],
)
def test_invalid_rows_enter_controlled_dead_letter_ledger(
    record: dict[str, object],
    reason: str,
) -> None:
    result = run_pipeline({"federal": [record], "municipal": []})

    assert result.opportunities.empty
    assert result.rejected["reason_code"].tolist() == [reason]
    assert result.rejected.loc[0, "source"] == "federal"
    assert result.rejected.loc[0, "source_row_id"]
    assert set(result.rejected) == {
        "source",
        "source_row_id",
        "reason_code",
        "detail",
    }
    assert repr(record) not in result.rejected.loc[0, "detail"]


def test_duplicate_winner_is_independent_of_input_order() -> None:
    older = federal_record(
        title="Earlier version",
        updated="2026-07-01T12:00:00Z",
    )
    newer_a = federal_record(
        title="New version A",
        updated="2026-07-04T12:00:00Z",
    )
    newer_b = federal_record(
        title="New version B",
        updated="2026-07-04T12:00:00Z",
    )

    forward = run_pipeline({"federal": [older, newer_a, newer_b], "municipal": []})
    reverse = run_pipeline({"federal": [newer_b, newer_a, older], "municipal": []})

    assert_frame_equal(forward.opportunities, reverse.opportunities)
    assert forward.manifest.canonical_hash == reverse.manifest.canonical_hash
    assert forward.opportunities.loc[0, "source_updated_at"] == ("2026-07-04T12:00:00Z")


def test_same_timestamp_hash_tie_break_is_stable_across_incremental_runs() -> None:
    timestamp = "2026-07-04T12:00:00.123456Z"
    version_a = federal_record(title="Version A", updated=timestamp)
    version_b = federal_record(title="Version B", updated=timestamp)

    first_a = run_pipeline({"federal": [version_a], "municipal": []})
    after_b = run_pipeline(
        {"federal": [version_b], "municipal": []},
        existing=first_a.opportunities,
        state=first_a.state,
    )
    first_b = run_pipeline({"federal": [version_b], "municipal": []})
    after_a = run_pipeline(
        {"federal": [version_a], "municipal": []},
        existing=first_b.opportunities,
        state=first_b.state,
    )

    assert_frame_equal(after_b.opportunities, after_a.opportunities)
    expected_hash = max(
        first_a.opportunities.loc[0, "content_hash"],
        first_b.opportunities.loc[0, "content_hash"],
    )
    assert after_b.opportunities.loc[0, "content_hash"] == expected_hash
    assert after_b.state == after_a.state


def test_fractional_update_timestamp_is_retained_in_output_and_state() -> None:
    result = run_pipeline(
        {
            "federal": [federal_record(updated="2026-07-04T12:00:00.123456Z")],
            "municipal": [],
        }
    )

    assert (
        result.opportunities.loc[0, "source_updated_at"]
        == "2026-07-04T12:00:00.123456Z"
    )
    assert result.state.watermarks["federal"] == "2026-07-04T12:00:00.123456Z"


def test_fractional_update_is_ordered_after_whole_second() -> None:
    whole_second = run_pipeline(
        {
            "federal": [
                federal_record(
                    title="Whole second",
                    updated="2026-07-04T12:00:00Z",
                )
            ],
            "municipal": [],
        }
    )
    fractional = run_pipeline(
        {
            "federal": [
                federal_record(
                    title="Fractional update",
                    updated="2026-07-04T12:00:00.000001Z",
                )
            ],
            "municipal": [],
        },
        existing=whole_second.opportunities,
        state=whole_second.state,
    )

    assert fractional.opportunities.loc[0, "title"] == "Fractional update"
    assert fractional.state.watermarks["federal"] == "2026-07-04T12:00:00.000001Z"


def test_stale_increment_cannot_overwrite_existing_newer_record() -> None:
    current = run_pipeline(
        {
            "federal": [
                federal_record(
                    title="Current title",
                    updated="2026-07-05T12:00:00Z",
                )
            ],
            "municipal": [],
        }
    )
    stale = run_pipeline(
        {
            "federal": [
                federal_record(
                    title="Stale title",
                    updated="2026-07-04T12:00:00Z",
                )
            ],
            "municipal": [],
        },
        existing=current.opportunities,
        state=current.state,
    )

    assert stale.opportunities.loc[0, "title"] == "Current title"
    assert stale.manifest.canonical_hash == current.manifest.canonical_hash
    assert stale.state == current.state
    assert stale.manifest.stale_count == 1


def test_same_increment_is_idempotent() -> None:
    fixture = generate_synthetic_sources(seed=2026)
    first = run_pipeline(fixture.batches)
    second = run_pipeline(
        fixture.batches,
        existing=first.opportunities,
        state=first.state,
    )

    assert_frame_equal(first.opportunities, second.opportunities)
    assert_frame_equal(first.rejected, second.rejected)
    assert second.state == first.state
    assert second.manifest.canonical_hash == first.manifest.canonical_hash
    assert second.manifest.rejection_hash == first.manifest.rejection_hash
    assert second.manifest.state_hash == first.manifest.state_hash


def test_watermark_advances_only_to_latest_accepted_timestamp() -> None:
    valid = federal_record(updated="2026-07-04T12:00:00Z")
    invalid_future = federal_record(
        source_id="FED-INVALID",
        closes="not-a-date",
        updated="2027-01-01T00:00:00Z",
    )

    result = run_pipeline(
        {"federal": [invalid_future, valid], "municipal": []},
        state=PipelineState(watermarks={"federal": "2026-07-01T00:00:00Z"}),
    )

    assert result.state.watermarks["federal"] == "2026-07-04T12:00:00Z"
    assert result.rejected["reason_code"].tolist() == ["invalid_date"]


def test_source_volume_is_bounded_before_processing() -> None:
    record = federal_record()
    oversized = [deepcopy(record) for _ in range(MAX_SOURCE_RECORDS + 1)]

    with pytest.raises(PipelineInputError, match="5,000"):
        run_pipeline({"federal": oversized, "municipal": []})


def test_source_volume_is_rejected_before_record_copying() -> None:
    class OversizedSequence(Sequence[dict[str, object]]):
        def __len__(self) -> int:
            return MAX_SOURCE_RECORDS + 1

        def __getitem__(self, index: int) -> dict[str, object]:
            raise AssertionError(f"oversized source was accessed at {index}")

    with pytest.raises(PipelineInputError, match="5,000"):
        run_pipeline({"federal": OversizedSequence(), "municipal": []})


def test_hostile_source_value_type_fails_before_dead_letter_hashing() -> None:
    class HostileValue:
        def __str__(self) -> str:
            raise AssertionError("hostile value was stringified")

    record = federal_record(source_id=None)
    record["notice_title"] = HostileValue()

    with pytest.raises(PipelineInputError, match="bounded primitive"):
        run_pipeline({"federal": [record], "municipal": []})


def test_oversized_source_text_fails_at_input_boundary() -> None:
    record = federal_record(title="x" * 10_001)

    with pytest.raises(PipelineInputError, match="10,000"):
        run_pipeline({"federal": [record], "municipal": []})


def test_oversized_source_number_fails_at_input_boundary() -> None:
    record = federal_record(maximum=10**1_000)

    with pytest.raises(PipelineInputError, match="numeric magnitude"):
        run_pipeline({"federal": [record], "municipal": []})


def test_unknown_source_fails_closed() -> None:
    with pytest.raises(PipelineInputError, match="unsupported source"):
        run_pipeline({"unknown": [federal_record()]})


def test_mixed_type_source_names_fail_closed() -> None:
    with pytest.raises(PipelineInputError, match="source names"):
        run_pipeline({1: [], "unknown": []})  # type: ignore[dict-item]


def test_existing_canonical_table_requires_version_columns() -> None:
    existing = pd.DataFrame([{"canonical_id": "federal:FED-001"}])

    with pytest.raises(PipelineInputError, match="existing"):
        run_pipeline(
            {"federal": [federal_record()], "municipal": []},
            existing=existing,
        )


def test_existing_canonical_content_identity_is_verified() -> None:
    current = run_pipeline(
        {"federal": [federal_record()], "municipal": []}
    ).opportunities
    tampered = current.copy(deep=True)
    tampered.loc[0, "title"] = "Changed without a new content identity"

    with pytest.raises(PipelineInputError, match="content identity"):
        run_pipeline(
            {"federal": [], "municipal": []},
            existing=tampered,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source", "unknown"),
        ("canonical_id", "federal:OTHER"),
        ("source_id", " FED-001 "),
        ("title", ""),
        ("agency", 7),
        ("published_date", "07/01/2026"),
        ("closing_date", "2026-06-30"),
        ("location_policy", "anywhere"),
        ("engagement_type", "employment"),
        ("value_min_usd", -1.0),
        ("value_min_usd", 300_000.0),
        ("value_max_usd", float("inf")),
        ("value_max_usd", 10**1_000),
        ("skill_tags", "python||gcp"),
        ("skill_tags", "x" * 10_001),
        ("source_updated_at", "2026-07-01T07:00:00-05:00"),
        ("schema_version", "2.0"),
    ],
)
def test_existing_canonical_rows_are_semantically_validated(
    field: str,
    value: object,
) -> None:
    existing = run_pipeline(
        {"federal": [federal_record()], "municipal": []}
    ).opportunities
    tampered = existing.copy(deep=True)
    tampered[field] = tampered[field].astype(object)
    tampered.at[0, field] = value
    row = tampered.iloc[0].to_dict()
    tampered.at[0, "content_hash"] = content_hash(
        {column: row[column] for column in tampered.columns if column != "content_hash"}
    )

    with pytest.raises(PipelineInputError, match="existing canonical data"):
        run_pipeline(
            {"federal": [], "municipal": []},
            existing=tampered,
        )
