from __future__ import annotations

import pandas as pd

from content_performance_classifier import (
    CONTENT_COLUMNS,
    CONTENT_TYPES,
    FIXTURE_VERSION,
    TOPIC_FAMILIES,
    generate_synthetic_content,
)


def test_synthetic_fixture_is_reproducible_and_content_addressed() -> None:
    first = generate_synthetic_content(seed=17, rows=320)
    second = generate_synthetic_content(seed=17, rows=320)
    changed = generate_synthetic_content(seed=18, rows=320)

    pd.testing.assert_frame_equal(first.frame, second.frame)
    assert first.fixture_hash == second.fixture_hash
    assert first.fixture_hash != changed.fixture_hash
    assert first.seed == 17
    assert first.rows == 320
    assert first.fixture_version == FIXTURE_VERSION


def test_synthetic_fixture_obeys_schema_and_ranges(fixture) -> None:
    frame = fixture.frame

    assert tuple(frame.columns) == CONTENT_COLUMNS
    assert len(frame) == 600
    assert frame["content_id"].is_unique
    assert frame["content_id"].notna().all()
    assert set(frame["topic_family"]).issubset(TOPIC_FAMILIES)
    assert set(frame["content_type"]).issubset(CONTENT_TYPES)
    assert frame["word_count"].between(200, 5_000).all()
    assert frame["readability_score"].between(0, 100).all()
    assert frame["age_days"].between(0, 2_000).all()
    assert frame["internal_link_count"].between(0, 100).all()
    assert frame["entity_count"].between(0, 100).all()
    assert frame["query_coverage"].between(0, 1).all()
    assert frame["update_cadence"].between(0, 24).all()
    assert set(frame["high_engagement"]) == {0, 1}
