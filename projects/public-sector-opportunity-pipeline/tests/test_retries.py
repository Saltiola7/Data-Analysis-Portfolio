from __future__ import annotations

import math
from collections.abc import Sequence

import pytest

from public_sector_opportunity_pipeline import (
    MAX_SOURCE_RECORDS,
    PermanentSourceError,
    PipelineInputError,
    RetryExhaustedError,
    RetryPolicy,
    TransientSourceError,
    fetch_with_retry,
    run_pipeline_from_adapters,
)

from .test_pipeline import federal_record, municipal_record


def test_transient_source_failure_retries_then_succeeds() -> None:
    calls = 0
    delays: list[float] = []

    def fetch() -> list[dict[str, str]]:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise TransientSourceError("temporary")
        return [{"notice_id": "FED-001"}]

    result = fetch_with_retry(
        "federal",
        fetch,
        policy=RetryPolicy(max_attempts=3, delays=(0.0, 0.0)),
        sleep=delays.append,
    )

    assert result.retry_count == 2
    assert calls == 3
    assert delays == [0.0, 0.0]
    assert result.records == ({"notice_id": "FED-001"},)


def test_transient_source_failure_exhausts_bounded_attempts() -> None:
    calls = 0

    def fetch() -> list[dict[str, str]]:
        nonlocal calls
        calls += 1
        raise TransientSourceError("temporary")

    with pytest.raises(RetryExhaustedError) as caught:
        fetch_with_retry(
            "municipal",
            fetch,
            policy=RetryPolicy(max_attempts=2, delays=(0.0,)),
            sleep=lambda _seconds: None,
        )

    assert calls == 2
    assert caught.value.source == "municipal"
    assert caught.value.attempts == 2


def test_permanent_source_failure_is_not_retried() -> None:
    calls = 0

    def fetch() -> list[dict[str, str]]:
        nonlocal calls
        calls += 1
        raise PermanentSourceError("denied")

    with pytest.raises(PermanentSourceError, match="denied"):
        fetch_with_retry(
            "federal",
            fetch,
            policy=RetryPolicy(max_attempts=3, delays=(0.0, 0.0)),
            sleep=lambda _seconds: None,
        )

    assert calls == 1


def test_source_adapters_feed_retry_counts_into_run_manifest() -> None:
    federal_calls = 0

    def fetch_federal() -> list[dict[str, object]]:
        nonlocal federal_calls
        federal_calls += 1
        if federal_calls == 1:
            raise TransientSourceError("temporary")
        return [federal_record()]

    result = run_pipeline_from_adapters(
        {
            "federal": fetch_federal,
            "municipal": lambda: [municipal_record()],
        },
        policy=RetryPolicy(max_attempts=2, delays=(0.0,)),
        sleep=lambda _seconds: None,
    )

    assert result.manifest.retry_counts == {
        "federal": 1,
        "municipal": 0,
    }
    assert result.manifest.output_count == 2


def test_adapter_source_volume_is_rejected_before_record_copying() -> None:
    class OversizedSequence(Sequence[dict[str, object]]):
        def __len__(self) -> int:
            return MAX_SOURCE_RECORDS + 1

        def __getitem__(self, index: int) -> dict[str, object]:
            raise AssertionError(f"oversized adapter result was accessed at {index}")

    with pytest.raises(PipelineInputError, match="5,000"):
        fetch_with_retry(
            "federal",
            OversizedSequence,
            sleep=lambda _seconds: None,
        )


@pytest.mark.parametrize(
    "policy",
    [
        RetryPolicy(max_attempts=0),
        RetryPolicy(max_attempts=3, delays=(0.0,)),
        RetryPolicy(max_attempts=2, delays=(-1.0,)),
        RetryPolicy(max_attempts=2, delays=(math.inf,)),
        RetryPolicy(max_attempts=2, delays=(math.nan,)),
    ],
)
def test_invalid_retry_policy_fails_at_boundary(policy: RetryPolicy) -> None:
    with pytest.raises(ValueError):
        fetch_with_retry("federal", lambda: [], policy=policy)
