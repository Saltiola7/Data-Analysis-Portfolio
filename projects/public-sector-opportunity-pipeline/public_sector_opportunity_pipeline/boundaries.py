"""Resource and type boundaries for untrusted in-memory source batches."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from public_sector_opportunity_pipeline.errors import PipelineInputError

MAX_SOURCE_RECORDS = 5_000
MAX_SOURCE_FIELDS = 32
MAX_SOURCE_TEXT_LENGTH = 10_000
MAX_SOURCE_SEQUENCE_ITEMS = 100
MAX_SOURCE_NUMERIC_MAGNITUDE = 10**15

SOURCE_FIELDS = {
    "federal": (
        "notice_id",
        "notice_title",
        "bureau",
        "published_on",
        "closes_on",
        "work_location",
        "award_type",
        "min_value_usd",
        "max_value_usd",
        "capabilities",
        "modified_at",
    ),
    "municipal": (
        "solicitation_number",
        "name",
        "department",
        "posted_at",
        "deadline",
        "remote_policy",
        "engagement_model",
        "budget_floor",
        "budget_ceiling",
        "required_skills",
        "updated_at",
    ),
}


def validate_source_sequence(
    source: str,
    records: object,
) -> Sequence[Mapping[str, object]]:
    """Validate sequence shape and volume without reading any record."""

    if isinstance(records, (str, bytes, bytearray)) or not isinstance(
        records,
        Sequence,
    ):
        raise PipelineInputError(f"{source} batch must be a sequence")
    if len(records) > MAX_SOURCE_RECORDS:
        raise PipelineInputError(
            "source batches exceed the 5,000-record processing limit"
        )
    return records


def copy_source_records(
    source: str,
    records: object,
) -> tuple[Mapping[str, object], ...]:
    """Copy one bounded batch using only source-contract fields and values."""

    sequence = validate_source_sequence(source, records)
    fields = SOURCE_FIELDS.get(source)
    if fields is None:
        raise PipelineInputError(f"unsupported source: {source}")

    copied: list[Mapping[str, object]] = []
    for record in sequence:
        if not isinstance(record, Mapping):
            raise PipelineInputError(f"{source} records must be field mappings")
        if len(record) > MAX_SOURCE_FIELDS:
            raise PipelineInputError(
                f"{source} records exceed the {MAX_SOURCE_FIELDS}-field limit"
            )
        copied.append(
            {
                field: _copy_public_value(record[field])
                for field in fields
                if field in record
            }
        )
    return tuple(copied)


def _copy_public_value(value: object) -> object:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        if abs(value) > MAX_SOURCE_NUMERIC_MAGNITUDE:
            raise PipelineInputError("source numeric magnitude exceeds the limit")
        return value
    if isinstance(value, float):
        if not math.isfinite(value) or abs(value) > MAX_SOURCE_NUMERIC_MAGNITUDE:
            raise PipelineInputError("source numeric magnitude exceeds the limit")
        return value
    if isinstance(value, str):
        if len(value) > MAX_SOURCE_TEXT_LENGTH:
            raise PipelineInputError("source text exceeds the 10,000-character limit")
        return value
    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        if len(value) > MAX_SOURCE_SEQUENCE_ITEMS:
            raise PipelineInputError("source sequence exceeds the 100-item limit")
        copied_items: list[object] = []
        for item in value:
            if not isinstance(item, (str, bool, int, float)) and item is not None:
                raise PipelineInputError(
                    "source values must use bounded primitive types"
                )
            copied_items.append(_copy_public_value(item))
        return tuple(copied_items)
    raise PipelineInputError("source values must use bounded primitive types")
