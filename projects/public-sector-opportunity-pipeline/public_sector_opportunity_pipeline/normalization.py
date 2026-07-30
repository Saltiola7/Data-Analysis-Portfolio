"""Source-specific normalization into the canonical opportunity schema."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime

from public_sector_opportunity_pipeline.boundaries import MAX_SOURCE_TEXT_LENGTH
from public_sector_opportunity_pipeline.errors import RecordValidationError
from public_sector_opportunity_pipeline.hashing import content_hash

SUPPORTED_SOURCES = ("federal", "municipal")
SUPPORTED_ENGAGEMENTS = ("consulting", "contract", "project")
SUPPORTED_LOCATIONS = ("flexible", "hybrid", "on-site", "remote")

FEDERAL_ENGAGEMENT_MAP = {
    "professional_services": "consulting",
    "task_order": "contract",
    "fixed_scope": "project",
}

CANONICAL_COLUMNS = [
    "canonical_id",
    "source",
    "source_id",
    "title",
    "agency",
    "published_date",
    "closing_date",
    "location_policy",
    "engagement_type",
    "value_min_usd",
    "value_max_usd",
    "skill_tags",
    "source_updated_at",
    "schema_version",
    "content_hash",
]

REJECTED_COLUMNS = [
    "source",
    "source_row_id",
    "reason_code",
    "detail",
]

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
_TAG_SEPARATOR = re.compile(r"[|,]")
_TAG_PUNCTUATION = re.compile(r"[^a-z0-9]+")


def normalize_record(
    source: str,
    record: Mapping[str, object],
) -> dict[str, object]:
    """Normalize one source row or raise a controlled validation error."""

    if source == "federal":
        normalized = _normalize_federal(record)
    elif source == "municipal":
        normalized = _normalize_municipal(record)
    else:
        raise RecordValidationError(
            "unsupported_source",
            "source schema is not supported",
        )

    normalized["canonical_id"] = f"{normalized['source']}:{normalized['source_id']}"
    normalized["schema_version"] = "1.0"
    normalized["content_hash"] = content_hash(normalized)
    return {column: normalized[column] for column in CANONICAL_COLUMNS}


def stable_source_row_id(
    source: str,
    record: Mapping[str, object],
) -> str:
    """Return source identity when safe, otherwise an anonymous content ID."""

    identity_keys = {
        "federal": "notice_id",
        "municipal": "solicitation_number",
    }
    identity = record.get(identity_keys.get(source, ""))
    if isinstance(identity, str) and identity.strip():
        return identity.strip()
    return f"anon-{content_hash({'source': source, 'record': record})[:12]}"


def parse_update_timestamp(value: object) -> str:
    """Validate a timezone-aware ISO timestamp and normalize it to UTC."""

    if not isinstance(value, str) or not _TIMESTAMP_PATTERN.fullmatch(value):
        raise RecordValidationError(
            "invalid_update_timestamp",
            "source update timestamp must be timezone-aware ISO-8601",
        )
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise RecordValidationError(
            "invalid_update_timestamp",
            "source update timestamp must be a valid calendar timestamp",
        ) from exc
    if parsed.tzinfo is None:
        raise RecordValidationError(
            "invalid_update_timestamp",
            "source update timestamp must include a timezone",
        )
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


def update_timestamp_key(value: object) -> datetime:
    """Return a comparable UTC datetime after canonical timestamp validation."""

    canonical = parse_update_timestamp(value)
    return datetime.fromisoformat(canonical)


def validate_canonical_record(record: Mapping[str, object]) -> None:
    """Validate every semantic and canonical-serialization invariant."""

    source = record.get("source")
    if not isinstance(source, str) or source not in SUPPORTED_SOURCES:
        raise RecordValidationError(
            "invalid_canonical_source",
            "canonical source is outside the supported set",
        )
    source_id = _canonical_text(record.get("source_id"), "source identity")
    title = _canonical_text(record.get("title"), "title")
    agency = _canonical_text(record.get("agency"), "agency")
    canonical_id = _canonical_text(record.get("canonical_id"), "canonical identity")
    if canonical_id != f"{source}:{source_id}":
        raise RecordValidationError(
            "invalid_canonical_identity",
            "canonical identity does not match source and source identity",
        )

    published = _calendar_date(record.get("published_date"))
    closing = _calendar_date(record.get("closing_date"))
    if closing < published:
        raise RecordValidationError(
            "inverted_closing_window",
            "closing date cannot precede published date",
        )

    location = _canonical_text(record.get("location_policy"), "location policy")
    if location not in SUPPORTED_LOCATIONS:
        raise RecordValidationError(
            "unsupported_location",
            "canonical location policy is outside the supported set",
        )
    engagement = _canonical_text(
        record.get("engagement_type"),
        "engagement type",
    )
    if engagement not in SUPPORTED_ENGAGEMENTS:
        raise RecordValidationError(
            "unsupported_engagement",
            "canonical engagement type is outside the supported set",
        )

    minimum = _money_value(record.get("value_min_usd"))
    maximum = _money_value(record.get("value_max_usd"))
    if minimum > maximum:
        raise RecordValidationError(
            "invalid_value_band",
            "minimum value cannot exceed maximum value",
        )

    tags_value = record.get("skill_tags")
    if (
        not isinstance(tags_value, str)
        or len(tags_value) > MAX_SOURCE_TEXT_LENGTH
        or "|".join(_skill_tags(tags_value)) != tags_value
    ):
        raise RecordValidationError(
            "invalid_canonical_tags",
            "canonical skill tags must be sorted normalized text",
        )

    timestamp = record.get("source_updated_at")
    if parse_update_timestamp(timestamp) != timestamp:
        raise RecordValidationError(
            "invalid_canonical_timestamp",
            "canonical update timestamp must be normalized to UTC",
        )
    if record.get("schema_version") != "1.0":
        raise RecordValidationError(
            "unsupported_schema_version",
            "canonical schema version is unsupported",
        )

    # Keep these bindings explicit: their successful validation is part of the
    # full-row semantic contract even though callers only need failure evidence.
    _ = title, agency


def _normalize_federal(record: Mapping[str, object]) -> dict[str, object]:
    engagement_raw = _required_text(record, "award_type")
    try:
        engagement = FEDERAL_ENGAGEMENT_MAP[engagement_raw]
    except KeyError as exc:
        raise RecordValidationError(
            "unsupported_engagement",
            "engagement type is outside the supported contract set",
        ) from exc

    return _canonical_values(
        source="federal",
        source_id=_identity(record, "notice_id"),
        title=_required_text(record, "notice_title"),
        agency=_required_text(record, "bureau"),
        published=record.get("published_on"),
        closing=record.get("closes_on"),
        location=record.get("work_location"),
        engagement=engagement,
        minimum=record.get("min_value_usd"),
        maximum=record.get("max_value_usd"),
        tags=record.get("capabilities"),
        updated=record.get("modified_at"),
    )


def _normalize_municipal(record: Mapping[str, object]) -> dict[str, object]:
    engagement = _required_text(record, "engagement_model")
    if engagement not in SUPPORTED_ENGAGEMENTS:
        raise RecordValidationError(
            "unsupported_engagement",
            "engagement type is outside the supported contract set",
        )

    return _canonical_values(
        source="municipal",
        source_id=_identity(record, "solicitation_number"),
        title=_required_text(record, "name"),
        agency=_required_text(record, "department"),
        published=record.get("posted_at"),
        closing=record.get("deadline"),
        location=record.get("remote_policy"),
        engagement=engagement,
        minimum=record.get("budget_floor"),
        maximum=record.get("budget_ceiling"),
        tags=record.get("required_skills"),
        updated=record.get("updated_at"),
    )


def _canonical_values(
    *,
    source: str,
    source_id: str,
    title: str,
    agency: str,
    published: object,
    closing: object,
    location: object,
    engagement: str,
    minimum: object,
    maximum: object,
    tags: object,
    updated: object,
) -> dict[str, object]:
    published_date = _calendar_date(published)
    closing_date = _calendar_date(closing)
    if closing_date < published_date:
        raise RecordValidationError(
            "inverted_closing_window",
            "closing date cannot precede published date",
        )

    location_policy = _required_text_value(location)
    if location_policy not in SUPPORTED_LOCATIONS:
        raise RecordValidationError(
            "unsupported_location",
            "location policy is outside the supported set",
        )

    value_min = _money_value(minimum)
    value_max = _money_value(maximum)
    if value_min > value_max:
        raise RecordValidationError(
            "invalid_value_band",
            "minimum value cannot exceed maximum value",
        )

    skill_tags = _skill_tags(tags)
    return {
        "source": source,
        "source_id": source_id,
        "title": title,
        "agency": agency,
        "published_date": published_date.isoformat(),
        "closing_date": closing_date.isoformat(),
        "location_policy": location_policy,
        "engagement_type": engagement,
        "value_min_usd": value_min,
        "value_max_usd": value_max,
        "skill_tags": "|".join(skill_tags),
        "source_updated_at": parse_update_timestamp(updated),
    }


def _identity(record: Mapping[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RecordValidationError(
            "missing_identity",
            "required source identity is absent",
        )
    return value.strip()


def _required_text(record: Mapping[str, object], key: str) -> str:
    return _required_text_value(record.get(key))


def _required_text_value(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RecordValidationError(
            "missing_field",
            "a required text field is absent",
        )
    return value.strip().casefold() if value.strip().islower() else value.strip()


def _canonical_text(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > MAX_SOURCE_TEXT_LENGTH
    ):
        raise RecordValidationError(
            "invalid_canonical_text",
            f"canonical {field} must be bounded nonempty text",
        )
    return value


def _calendar_date(value: object) -> date:
    if not isinstance(value, str) or not _DATE_PATTERN.fullmatch(value):
        raise RecordValidationError(
            "invalid_date",
            "date must use YYYY-MM-DD calendar format",
        )
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise RecordValidationError(
            "invalid_date",
            "date must be a valid calendar date",
        ) from exc


def _money_value(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RecordValidationError(
            "invalid_value",
            "opportunity values must be finite non-negative numbers",
        )
    try:
        numeric = float(value)
    except (OverflowError, ValueError) as exc:
        raise RecordValidationError(
            "invalid_value",
            "opportunity values must be finite non-negative numbers",
        ) from exc
    if not math.isfinite(numeric) or numeric < 0:
        raise RecordValidationError(
            "invalid_value",
            "opportunity values must be finite non-negative numbers",
        )
    return numeric


def _skill_tags(value: object) -> tuple[str, ...]:
    raw_tags: Sequence[object]
    if isinstance(value, str):
        raw_tags = _TAG_SEPARATOR.split(value)
    elif isinstance(value, Sequence) and not isinstance(
        value,
        (bytes, bytearray),
    ):
        raw_tags = value
    else:
        raise RecordValidationError(
            "missing_field",
            "skill tags are required",
        )

    tags = {
        _TAG_PUNCTUATION.sub("-", raw.casefold()).strip("-")
        for raw in raw_tags
        if isinstance(raw, str) and raw.strip()
    }
    tags.discard("")
    if not tags:
        raise RecordValidationError(
            "missing_field",
            "at least one skill tag is required",
        )
    return tuple(sorted(tags))
