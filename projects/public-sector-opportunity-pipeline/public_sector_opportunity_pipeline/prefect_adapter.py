"""Optional Prefect orchestration adapter over the portable core."""

from __future__ import annotations

import pandas as pd
from prefect import flow, task

from public_sector_opportunity_pipeline.models import (
    PipelineResult,
    PipelineState,
    SourceFixture,
)
from public_sector_opportunity_pipeline.pipeline import run_pipeline


@task(name="normalize-merge-audit", log_prints=False)
def execute_core_task(
    source_fixture: SourceFixture,
    existing_frame: pd.DataFrame | None,
    pipeline_state: PipelineState | None,
) -> PipelineResult:
    """Execute portable core at one explicit Prefect task boundary."""

    return _execute_core(source_fixture, existing_frame, pipeline_state)


@flow(name="public-sector-opportunity-pipeline", log_prints=False)
def opportunity_flow(
    source_fixture: SourceFixture,
    existing_frame: pd.DataFrame | None = None,
    pipeline_state: PipelineState | None = None,
) -> PipelineResult:
    """Orchestrate one deterministic pipeline run."""

    return execute_core_task(source_fixture, existing_frame, pipeline_state)


def run_prefect_pipeline(
    fixture: SourceFixture,
    *,
    existing: pd.DataFrame | None = None,
    state: PipelineState | None = None,
    use_engine: bool = False,
) -> PipelineResult:
    """Run core parity locally, optionally through a configured Prefect engine."""

    if use_engine:
        return opportunity_flow(fixture, existing, state)
    return _execute_core(fixture, existing, state)


def build_prefect_flow():
    """Return the deployable Prefect flow for inspection or registration."""

    return opportunity_flow


def _execute_core(
    fixture: SourceFixture,
    existing: pd.DataFrame | None,
    state: PipelineState | None,
) -> PipelineResult:
    return run_pipeline(
        fixture.batches,
        existing=existing,
        state=state,
        fixture_version=fixture.version,
        seed=fixture.seed,
        retry_counts={source: 0 for source in fixture.batches},
    )
