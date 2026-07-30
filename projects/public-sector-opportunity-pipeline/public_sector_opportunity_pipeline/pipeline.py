"""Deterministic normalization, incremental merge, and audit pipeline."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd

from public_sector_opportunity_pipeline.boundaries import (
    MAX_SOURCE_RECORDS,
    copy_source_records,
    validate_source_sequence,
)
from public_sector_opportunity_pipeline.errors import (
    PipelineInputError,
    RecordValidationError,
)
from public_sector_opportunity_pipeline.hashing import (
    content_hash,
    dataframe_hash,
)
from public_sector_opportunity_pipeline.models import (
    PipelineResult,
    PipelineState,
    RunManifest,
)
from public_sector_opportunity_pipeline.normalization import (
    CANONICAL_COLUMNS,
    REJECTED_COLUMNS,
    SUPPORTED_SOURCES,
    normalize_record,
    parse_update_timestamp,
    stable_source_row_id,
    update_timestamp_key,
    validate_canonical_record,
)

OUTPUT_GRAIN = "one row per source and source_id"


def run_pipeline(
    source_batches: Mapping[str, Sequence[Mapping[str, object]]],
    *,
    existing: pd.DataFrame | None = None,
    state: PipelineState | None = None,
    fixture_version: str = "external-v1",
    seed: int | None = None,
    retry_counts: Mapping[str, int] | None = None,
) -> PipelineResult:
    """Normalize, validate, incrementally merge, and audit source batches."""

    batches = _validate_source_batches(source_batches)
    existing_frame = _validate_existing(existing)
    state_before = _validated_state(state or PipelineState())
    watermarks = _watermarks_with_existing(
        dict(state_before.watermarks),
        existing_frame,
    )
    rejected_rows: list[dict[str, str]] = []
    eligible_rows: list[dict[str, object]] = []
    stale_count = 0

    for source in sorted(batches):
        watermark = watermarks.get(source)
        for record in batches[source]:
            try:
                normalized = normalize_record(source, record)
            except RecordValidationError as exc:
                rejected_rows.append(
                    {
                        "source": source,
                        "source_row_id": stable_source_row_id(source, record),
                        "reason_code": exc.reason_code,
                        "detail": exc.detail,
                    }
                )
                continue

            if watermark and update_timestamp_key(
                normalized["source_updated_at"]
            ) < update_timestamp_key(watermark):
                stale_count += 1
                continue
            eligible_rows.append(normalized)

    incoming = _deduplicate(eligible_rows)
    merged = _merge(existing_frame, incoming)
    next_watermarks = _advance_watermarks(watermarks, incoming)
    rejected = _rejected_frame(rejected_rows)
    next_state = PipelineState(
        schema_version=state_before.schema_version,
        watermarks=next_watermarks,
    )
    manifest = _manifest(
        fixture_version=fixture_version,
        seed=seed,
        input_count=sum(len(batch) for batch in batches.values()),
        accepted_count=len(incoming),
        stale_count=stale_count,
        opportunities=merged,
        rejected=rejected,
        state_before=state_before,
        state_after=next_state,
        retry_counts=retry_counts,
    )
    return PipelineResult(
        opportunities=merged,
        rejected=rejected,
        state=next_state,
        manifest=manifest,
    )


def _validate_source_batches(
    source_batches: Mapping[str, Sequence[Mapping[str, object]]],
) -> dict[str, tuple[Mapping[str, object], ...]]:
    if not isinstance(source_batches, Mapping):
        raise PipelineInputError("source batches must be a mapping")
    if any(not isinstance(source, str) for source in source_batches):
        raise PipelineInputError("source names must be strings")
    unsupported = sorted(set(source_batches) - set(SUPPORTED_SOURCES))
    if unsupported:
        raise PipelineInputError(
            f"unsupported source: {', '.join(str(item) for item in unsupported)}"
        )

    sequences: dict[str, Sequence[Mapping[str, object]]] = {}
    total = 0
    for source, records in source_batches.items():
        sequence = validate_source_sequence(source, records)
        sequences[source] = sequence
        total += len(sequence)

    if total > MAX_SOURCE_RECORDS:
        raise PipelineInputError(
            "source batches exceed the 5,000-record processing limit"
        )
    return {
        source: copy_source_records(source, records)
        for source, records in sequences.items()
    }


def _validate_existing(existing: pd.DataFrame | None) -> pd.DataFrame:
    if existing is None:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)
    if not isinstance(existing, pd.DataFrame):
        raise PipelineInputError("existing canonical data must be a DataFrame")
    missing = [column for column in CANONICAL_COLUMNS if column not in existing]
    if missing:
        raise PipelineInputError(
            "existing canonical data is missing required version columns"
        )
    frame = existing.loc[:, CANONICAL_COLUMNS].copy(deep=True)
    if frame["canonical_id"].duplicated().any():
        raise PipelineInputError(
            "existing canonical data contains duplicate identities"
        )
    for row in frame.to_dict("records"):
        try:
            validate_canonical_record(row)
        except RecordValidationError as exc:
            raise PipelineInputError(
                "existing canonical data violates canonical row semantics"
            ) from exc
        expected_hash = content_hash(
            {
                column: row[column]
                for column in CANONICAL_COLUMNS
                if column != "content_hash"
            }
        )
        if row["content_hash"] != expected_hash:
            raise PipelineInputError(
                "existing canonical data content identity does not match its row"
            )
    return _canonical_frame(frame.to_dict("records"))


def _validated_state(state: PipelineState) -> PipelineState:
    if state.schema_version != "1.0":
        raise PipelineInputError("pipeline state schema version is unsupported")
    unsupported = sorted(set(state.watermarks) - set(SUPPORTED_SOURCES))
    if unsupported:
        raise PipelineInputError("pipeline state contains an unsupported source")
    normalized: dict[str, str] = {}
    for source, timestamp in state.watermarks.items():
        try:
            normalized[source] = parse_update_timestamp(timestamp)
        except RecordValidationError as exc:
            raise PipelineInputError(
                "pipeline state contains an invalid watermark"
            ) from exc
    return PipelineState(schema_version="1.0", watermarks=normalized)


def _watermarks_with_existing(
    watermarks: dict[str, str],
    existing: pd.DataFrame,
) -> dict[str, str]:
    next_watermarks = dict(watermarks)
    if existing.empty:
        return next_watermarks
    for source, group in existing.groupby("source", sort=True):
        timestamps = group["source_updated_at"].tolist()
        existing_max = max(timestamps, key=update_timestamp_key)
        candidates = [existing_max]
        if source in next_watermarks:
            candidates.append(next_watermarks[source])
        next_watermarks[source] = max(
            candidates,
            key=update_timestamp_key,
        )
    return next_watermarks


def _deduplicate(rows: Sequence[Mapping[str, object]]) -> pd.DataFrame:
    winners: dict[str, dict[str, object]] = {}
    for row in rows:
        copied = dict(row)
        identity = str(copied["canonical_id"])
        previous = winners.get(identity)
        if previous is None or _version_key(copied) > _version_key(previous):
            winners[identity] = copied
    return _canonical_frame(winners.values())


def _merge(existing: pd.DataFrame, incoming: pd.DataFrame) -> pd.DataFrame:
    winners = {
        str(row["canonical_id"]): dict(row) for row in existing.to_dict("records")
    }
    for row in incoming.to_dict("records"):
        identity = str(row["canonical_id"])
        previous = winners.get(identity)
        if previous is None or _version_key(row) > _version_key(previous):
            winners[identity] = row
    return _canonical_frame(winners.values())


def _version_key(row: Mapping[str, object]) -> tuple[object, str]:
    return update_timestamp_key(row["source_updated_at"]), str(row["content_hash"])


def _canonical_frame(
    rows: Sequence[Mapping[str, object]] | object,
) -> pd.DataFrame:
    frame = pd.DataFrame(list(rows), columns=CANONICAL_COLUMNS)
    if frame.empty:
        return frame
    return (
        frame.sort_values("canonical_id", kind="stable")
        .reset_index(drop=True)
        .loc[:, CANONICAL_COLUMNS]
    )


def _rejected_frame(rows: Sequence[Mapping[str, str]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=REJECTED_COLUMNS)
    if frame.empty:
        return frame
    return (
        frame.sort_values(
            ["source", "source_row_id", "reason_code", "detail"],
            kind="stable",
        )
        .reset_index(drop=True)
        .loc[:, REJECTED_COLUMNS]
    )


def _advance_watermarks(
    watermarks: Mapping[str, str],
    incoming: pd.DataFrame,
) -> dict[str, str]:
    next_watermarks = dict(watermarks)
    if incoming.empty:
        return next_watermarks
    for source, group in incoming.groupby("source", sort=True):
        timestamps = group["source_updated_at"].tolist()
        accepted_max = max(timestamps, key=update_timestamp_key)
        candidates = [accepted_max]
        if source in next_watermarks:
            candidates.append(next_watermarks[source])
        next_watermarks[source] = max(
            candidates,
            key=update_timestamp_key,
        )
    return dict(sorted(next_watermarks.items()))


def _manifest(
    *,
    fixture_version: str,
    seed: int | None,
    input_count: int,
    accepted_count: int,
    stale_count: int,
    opportunities: pd.DataFrame,
    rejected: pd.DataFrame,
    state_before: PipelineState,
    state_after: PipelineState,
    retry_counts: Mapping[str, int] | None,
) -> RunManifest:
    state_payload = {
        "schema_version": state_after.schema_version,
        "watermarks": dict(sorted(state_after.watermarks.items())),
    }
    return RunManifest(
        schema_version="1.0",
        fixture_version=fixture_version,
        seed=seed,
        input_count=input_count,
        accepted_count=accepted_count,
        rejected_count=len(rejected),
        stale_count=stale_count,
        output_count=len(opportunities),
        retry_counts=_validated_retry_counts(retry_counts or {}),
        state_before=dict(sorted(state_before.watermarks.items())),
        state_after=dict(sorted(state_after.watermarks.items())),
        output_grain=OUTPUT_GRAIN,
        canonical_hash=dataframe_hash(opportunities),
        rejection_hash=dataframe_hash(rejected),
        state_hash=content_hash(state_payload),
    )


def _validated_retry_counts(
    retry_counts: Mapping[str, int],
) -> dict[str, int]:
    validated: dict[str, int] = {}
    for source, count in retry_counts.items():
        if source not in SUPPORTED_SOURCES:
            raise PipelineInputError("retry counts contain an unsupported source")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise PipelineInputError("retry counts must be non-negative integers")
        validated[source] = count
    return dict(sorted(validated.items()))
