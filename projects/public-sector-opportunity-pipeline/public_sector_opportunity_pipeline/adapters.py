"""Bounded source adapters feeding the deterministic pipeline."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence

import pandas as pd

from public_sector_opportunity_pipeline.errors import PipelineInputError
from public_sector_opportunity_pipeline.models import (
    PipelineResult,
    PipelineState,
    RetryPolicy,
)
from public_sector_opportunity_pipeline.normalization import SUPPORTED_SOURCES
from public_sector_opportunity_pipeline.pipeline import run_pipeline
from public_sector_opportunity_pipeline.retries import fetch_with_retry

SourceFetch = Callable[[], Sequence[Mapping[str, object]]]


def run_pipeline_from_adapters(
    adapters: Mapping[str, SourceFetch],
    *,
    policy: RetryPolicy | None = None,
    sleep: Callable[[float], None] = time.sleep,
    existing: pd.DataFrame | None = None,
    state: PipelineState | None = None,
) -> PipelineResult:
    """Fetch supported sources, record retries, then invoke portable core."""

    if not isinstance(adapters, Mapping):
        raise PipelineInputError("source adapters must be a mapping")
    unsupported = sorted(set(adapters) - set(SUPPORTED_SOURCES))
    if unsupported:
        raise PipelineInputError(
            f"unsupported source adapter: {', '.join(unsupported)}"
        )
    if any(not callable(fetch) for fetch in adapters.values()):
        raise PipelineInputError("each source adapter must be callable")

    batches: dict[str, Sequence[Mapping[str, object]]] = {}
    retry_counts: dict[str, int] = {}
    for source in sorted(adapters):
        fetched = fetch_with_retry(
            source,
            adapters[source],
            policy=policy,
            sleep=sleep,
        )
        batches[source] = fetched.records
        retry_counts[source] = fetched.retry_count

    return run_pipeline(
        batches,
        existing=existing,
        state=state,
        fixture_version="adapter-v1",
        retry_counts=retry_counts,
    )
