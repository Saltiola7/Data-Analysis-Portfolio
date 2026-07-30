"""Deterministic clean-room public-sector opportunity pipeline."""

from public_sector_opportunity_pipeline.adapters import (
    run_pipeline_from_adapters,
)
from public_sector_opportunity_pipeline.errors import (
    PermanentSourceError,
    PipelineInputError,
    RetryExhaustedError,
    TransientSourceError,
)
from public_sector_opportunity_pipeline.exports import (
    dataframe_to_safe_csv,
    manifest_to_json,
)
from public_sector_opportunity_pipeline.models import (
    FetchResult,
    FitPreferences,
    PipelineResult,
    PipelineState,
    RetryPolicy,
    RunManifest,
    SourceFixture,
)
from public_sector_opportunity_pipeline.pipeline import (
    MAX_SOURCE_RECORDS,
    run_pipeline,
)
from public_sector_opportunity_pipeline.retries import fetch_with_retry
from public_sector_opportunity_pipeline.scoring import score_opportunities
from public_sector_opportunity_pipeline.synthetic import (
    generate_synthetic_sources,
)

__all__ = [
    "MAX_SOURCE_RECORDS",
    "FetchResult",
    "FitPreferences",
    "PermanentSourceError",
    "PipelineInputError",
    "PipelineResult",
    "PipelineState",
    "RetryExhaustedError",
    "RetryPolicy",
    "RunManifest",
    "SourceFixture",
    "TransientSourceError",
    "dataframe_to_safe_csv",
    "fetch_with_retry",
    "generate_synthetic_sources",
    "manifest_to_json",
    "run_pipeline",
    "run_pipeline_from_adapters",
    "score_opportunities",
]
