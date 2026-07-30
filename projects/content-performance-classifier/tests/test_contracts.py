from __future__ import annotations

import pandas as pd
import pytest

from content_performance_classifier import (
    FEATURE_ALLOWLIST,
    InputValidationError,
    generate_synthetic_content,
    train_classifier,
)


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("readability_score", 101.0, "readability_score"),
        ("query_coverage", -0.01, "query_coverage"),
        ("word_count", 199, "word_count"),
        ("high_engagement", 2, "high_engagement"),
    ],
)
def test_invalid_ranges_fail_closed(column: str, value: object, message: str) -> None:
    frame = generate_synthetic_content(rows=120).frame
    frame.loc[0, column] = value

    with pytest.raises(InputValidationError, match=message):
        train_classifier(frame)


def test_missing_duplicate_and_oversized_inputs_fail_closed() -> None:
    frame = generate_synthetic_content(rows=120).frame

    with pytest.raises(InputValidationError, match="content_type"):
        train_classifier(frame.drop(columns=["content_type"]))

    duplicated = frame.copy()
    duplicated.loc[1, "content_id"] = duplicated.loc[0, "content_id"]
    with pytest.raises(InputValidationError, match="unique"):
        train_classifier(duplicated)

    oversized = pd.concat([frame] * 42, ignore_index=True).head(5_001)
    oversized["content_id"] = [f"oversized-{index}" for index in range(len(oversized))]
    with pytest.raises(InputValidationError, match="5,000"):
        train_classifier(oversized)


def test_training_does_not_mutate_input(fixture) -> None:
    source = fixture.frame.copy(deep=True)
    expected = source.copy(deep=True)

    train_classifier(source)

    pd.testing.assert_frame_equal(source, expected)


def test_explicit_allowlist_excludes_target_identifiers_and_proxies(fixture) -> None:
    frame = fixture.frame.assign(
        future_engagement=fixture.frame["high_engagement"],
        split_marker="test",
        body_text="synthetic prose",
    )

    artifact = train_classifier(frame)

    assert artifact.feature_columns == FEATURE_ALLOWLIST
    assert "content_id" not in artifact.feature_columns
    assert "high_engagement" not in artifact.feature_columns
    assert "future_engagement" not in artifact.feature_columns
    assert "split_marker" not in artifact.feature_columns
    assert "body_text" not in artifact.feature_columns


def test_training_recomputes_fixture_identity_after_valid_changes(fixture) -> None:
    frame = fixture.frame.copy(deep=True)
    frame.loc[0, "word_count"] = int(frame.loc[0, "word_count"]) + 1

    artifact = train_classifier(frame)

    assert artifact.fixture_hash == artifact.source_hash
    assert artifact.fixture_hash != fixture.fixture_hash


def test_three_way_split_requires_five_rows_per_target_class(fixture) -> None:
    sparse = pd.concat(
        [
            fixture.frame.loc[fixture.frame["high_engagement"] == 0].head(4),
            fixture.frame.loc[fixture.frame["high_engagement"] == 1].head(16),
        ],
        ignore_index=True,
    )

    with pytest.raises(InputValidationError, match="five rows"):
        train_classifier(sparse)


def test_three_way_split_accepts_five_rows_in_minority_class(fixture) -> None:
    boundary = pd.concat(
        [
            fixture.frame.loc[fixture.frame["high_engagement"] == 0].head(5),
            fixture.frame.loc[fixture.frame["high_engagement"] == 1].head(15),
        ],
        ignore_index=True,
    )

    artifact = train_classifier(boundary)

    assert len(artifact.train_ids) == 12
    assert len(artifact.validation_ids) == 4
    assert len(artifact.test_ids) == 4
