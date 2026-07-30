"""Side-effect-free bounded retry adapter for source fetch functions."""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Mapping, Sequence

from public_sector_opportunity_pipeline.boundaries import copy_source_records
from public_sector_opportunity_pipeline.errors import (
    RetryExhaustedError,
    TransientSourceError,
)
from public_sector_opportunity_pipeline.models import FetchResult, RetryPolicy

MAX_RETRY_ATTEMPTS = 10


def fetch_with_retry(
    source: str,
    fetch: Callable[[], Sequence[Mapping[str, object]]],
    *,
    policy: RetryPolicy | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> FetchResult:
    """Fetch with bounded retries for explicitly transient failures only."""

    selected = policy or RetryPolicy()
    _validate_policy(selected)

    for attempt in range(1, selected.max_attempts + 1):
        try:
            records = fetch()
        except TransientSourceError as exc:
            if attempt == selected.max_attempts:
                raise RetryExhaustedError(source, attempt) from exc
            sleep(selected.delays[attempt - 1])
            continue

        copied = copy_source_records(source, records)
        return FetchResult(records=copied, retry_count=attempt - 1)

    raise AssertionError("validated retry loop must return or raise")


def _validate_policy(policy: RetryPolicy) -> None:
    if (
        isinstance(policy.max_attempts, bool)
        or not isinstance(policy.max_attempts, int)
        or policy.max_attempts < 1
        or policy.max_attempts > MAX_RETRY_ATTEMPTS
    ):
        raise ValueError("max_attempts must be an integer from 1 through 10")
    if len(policy.delays) != policy.max_attempts - 1:
        raise ValueError("delays must provide one value between each attempt")
    if any(
        isinstance(delay, bool)
        or not isinstance(delay, (int, float))
        or delay < 0
        or not math.isfinite(float(delay))
        for delay in policy.delays
    ):
        raise ValueError("retry delays must be finite non-negative numbers")
