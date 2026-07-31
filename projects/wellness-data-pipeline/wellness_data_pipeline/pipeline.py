"""Deterministic, in-memory wellness data pipeline."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import asdict
from datetime import date, datetime
from typing import Any, Final

import pandas as pd

from .models import NormalizationError, PipelineResult, SchemaError, SourceProfile
from .normalization import (
    normalize_dose_mg,
    normalize_duration,
    normalize_nonnegative_number,
)

SCHEMA_VERSION: Final = "1.1"
MAX_INPUT_ROWS: Final = 10_000

PARTICIPANT_COLUMNS: Final[tuple[str, ...]] = (
    "participant_id",
    "cohort",
    "joined_on",
)
DAILY_SIGNAL_COLUMNS: Final[tuple[str, ...]] = (
    "participant_id",
    "observed_on",
    "sleep_value",
    "sleep_unit",
    "active_value",
    "active_unit",
    "pulse_bpm",
)
PROGRAM_COLUMNS: Final[tuple[str, ...]] = (
    "program_id",
    "program_name",
    "program_type",
)
INTERVENTION_COLUMNS: Final[tuple[str, ...]] = (
    "intervention_id",
    "participant_id",
    "program_id",
    "occurred_on",
    "intervention",
    "dose_value",
    "dose_unit",
)
PARTICIPANT_DAY_COLUMNS: Final[tuple[str, ...]] = (
    "participant_id",
    "observed_on",
    "cohort",
    "sleep_minutes",
    "active_minutes",
    "average_pulse_bpm",
    "intervention_event_count",
    "distinct_program_count",
    "total_intervention_dose_mg",
    "quality_status",
)
REJECTED_COLUMNS: Final[tuple[str, ...]] = (
    "source",
    "source_row_id",
    "reason_code",
    "detail",
)
SOURCE_ORDER: Final = {
    "participants": 0,
    "programs": 1,
    "daily_signals": 2,
    "interventions": 3,
}
ISO_DATE_PATTERN: Final = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _copy_and_require_columns(
    frame: pd.DataFrame,
    source: str,
    required_columns: tuple[str, ...],
) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise SchemaError(f"{source} must be a pandas DataFrame")
    copied = frame.copy(deep=True)
    if len(copied) > MAX_INPUT_ROWS:
        raise SchemaError(f"{source} exceeds the maximum of {MAX_INPUT_ROWS:,} data rows")
    missing = sorted(set(required_columns).difference(copied.columns))
    if missing:
        raise SchemaError(f"{source} missing required columns: {', '.join(missing)}")
    return copied


def _nonempty_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _iso_date(value: object) -> str | None:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if not isinstance(value, str) or ISO_DATE_PATTERN.fullmatch(value) is None:
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    return parsed.isoformat()


def _source_row_id(source: str, position: int) -> str:
    return f"{source}:{position:06d}"


def _reject(
    rejected: list[dict[str, Any]],
    *,
    source: str,
    position: int,
    reason_code: str,
    detail: str,
) -> None:
    rejected.append(
        {
            "source": source,
            "source_row_id": _source_row_id(source, position),
            "reason_code": reason_code,
            "detail": detail,
            "_source_order": SOURCE_ORDER[source],
            "_row_position": position,
        }
    )


def _canonical_hash(frame: pd.DataFrame) -> str:
    serialized = frame.to_csv(
        index=False,
        lineterminator="\n",
        float_format="%.17g",
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _process_participants(
    participants: pd.DataFrame,
    rejected: list[dict[str, Any]],
) -> dict[str, dict[str, str]]:
    normalized_ids = [_nonempty_string(value) for value in participants["participant_id"]]
    duplicate_ids = {
        participant_id
        for participant_id, count in Counter(
            participant_id for participant_id in normalized_ids if participant_id is not None
        ).items()
        if count > 1
    }
    accepted: dict[str, dict[str, str]] = {}

    for position, (_, row) in enumerate(participants.iterrows()):
        participant_id = normalized_ids[position]
        if participant_id is None:
            _reject(
                rejected,
                source="participants",
                position=position,
                reason_code="invalid_participant_id",
                detail="participant_id must be a nonempty string",
            )
            continue
        if participant_id in duplicate_ids:
            _reject(
                rejected,
                source="participants",
                position=position,
                reason_code="duplicate_participant_id",
                detail="participant_id occurs more than once",
            )
            continue
        joined_on = _iso_date(row["joined_on"])
        if joined_on is None:
            _reject(
                rejected,
                source="participants",
                position=position,
                reason_code="invalid_date",
                detail="joined_on must be an ISO calendar date",
            )
            continue
        cohort = _nonempty_string(row["cohort"])
        if cohort is None:
            _reject(
                rejected,
                source="participants",
                position=position,
                reason_code="invalid_cohort",
                detail="cohort must be a nonempty string",
            )
            continue
        accepted[participant_id] = {
            "participant_id": participant_id,
            "cohort": cohort,
            "joined_on": joined_on,
        }

    return accepted


def _process_programs(
    programs: pd.DataFrame,
    rejected: list[dict[str, Any]],
) -> dict[str, dict[str, str]]:
    normalized_ids = [_nonempty_string(value) for value in programs["program_id"]]
    duplicate_ids = {
        program_id
        for program_id, count in Counter(
            program_id for program_id in normalized_ids if program_id is not None
        ).items()
        if count > 1
    }
    accepted: dict[str, dict[str, str]] = {}
    for position, (_, row) in enumerate(programs.iterrows()):
        program_id = normalized_ids[position]
        if program_id is None:
            _reject(
                rejected,
                source="programs",
                position=position,
                reason_code="invalid_program_id",
                detail="program_id must be a nonempty string",
            )
            continue
        if program_id in duplicate_ids:
            _reject(
                rejected,
                source="programs",
                position=position,
                reason_code="duplicate_program_id",
                detail="program_id occurs more than once",
            )
            continue
        program_name = _nonempty_string(row["program_name"])
        program_type = _nonempty_string(row["program_type"])
        if program_name is None or program_type is None:
            _reject(
                rejected,
                source="programs",
                position=position,
                reason_code="invalid_program",
                detail="program_name and program_type must be nonempty strings",
            )
            continue
        accepted[program_id] = {
            "program_id": program_id,
            "program_name": program_name,
            "program_type": program_type,
        }
    return accepted


def _signal_keys(daily_signals: pd.DataFrame) -> list[tuple[str, str] | None]:
    keys: list[tuple[str, str] | None] = []
    for _, row in daily_signals.iterrows():
        participant_id = _nonempty_string(row["participant_id"])
        observed_on = _iso_date(row["observed_on"])
        if participant_id is None or observed_on is None:
            keys.append(None)
        else:
            keys.append((participant_id, observed_on))
    return keys


def _process_daily_signals(
    daily_signals: pd.DataFrame,
    accepted_participants: dict[str, dict[str, str]],
    rejected: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    signal_keys = _signal_keys(daily_signals)
    duplicate_keys = {
        key
        for key, count in Counter(key for key in signal_keys if key is not None).items()
        if count > 1
    }
    accepted: list[dict[str, Any]] = []

    for position, (_, row) in enumerate(daily_signals.iterrows()):
        participant_id = _nonempty_string(row["participant_id"])
        if participant_id is None:
            _reject(
                rejected,
                source="daily_signals",
                position=position,
                reason_code="invalid_participant_id",
                detail="participant_id must be a nonempty string",
            )
            continue
        observed_on = _iso_date(row["observed_on"])
        if observed_on is None:
            _reject(
                rejected,
                source="daily_signals",
                position=position,
                reason_code="invalid_date",
                detail="observed_on must be an ISO calendar date",
            )
            continue
        if (participant_id, observed_on) in duplicate_keys:
            _reject(
                rejected,
                source="daily_signals",
                position=position,
                reason_code="duplicate_signal_key",
                detail="participant_id and observed_on occur more than once",
            )
            continue
        if participant_id not in accepted_participants:
            _reject(
                rejected,
                source="daily_signals",
                position=position,
                reason_code="unknown_participant",
                detail="participant_id has no accepted participant row",
            )
            continue
        try:
            sleep_minutes = normalize_duration(row["sleep_value"], row["sleep_unit"])
            active_minutes = normalize_duration(row["active_value"], row["active_unit"])
            pulse_bpm = normalize_nonnegative_number(row["pulse_bpm"])
        except NormalizationError as exc:
            _reject(
                rejected,
                source="daily_signals",
                position=position,
                reason_code=exc.reason_code,
                detail=str(exc),
            )
            continue
        accepted.append(
            {
                "participant_id": participant_id,
                "observed_on": observed_on,
                "sleep_minutes": sleep_minutes,
                "active_minutes": active_minutes,
                "average_pulse_bpm": pulse_bpm,
            }
        )

    return accepted


def _intervention_ids(interventions: pd.DataFrame) -> list[str | None]:
    return [_nonempty_string(value) for value in interventions["intervention_id"]]


def _process_interventions(
    interventions: pd.DataFrame,
    accepted_participants: dict[str, dict[str, str]],
    accepted_programs: dict[str, dict[str, str]],
    accepted_signal_keys: set[tuple[str, str]],
    rejected: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    intervention_ids = _intervention_ids(interventions)
    duplicate_ids = {
        intervention_id
        for intervention_id, count in Counter(
            intervention_id for intervention_id in intervention_ids if intervention_id is not None
        ).items()
        if count > 1
    }
    accepted: list[dict[str, Any]] = []

    for position, (_, row) in enumerate(interventions.iterrows()):
        intervention_id = intervention_ids[position]
        if intervention_id is None:
            _reject(
                rejected,
                source="interventions",
                position=position,
                reason_code="invalid_intervention_id",
                detail="intervention_id must be a nonempty string",
            )
            continue
        if intervention_id in duplicate_ids:
            _reject(
                rejected,
                source="interventions",
                position=position,
                reason_code="duplicate_intervention_id",
                detail="intervention_id occurs more than once",
            )
            continue
        participant_id = _nonempty_string(row["participant_id"])
        if participant_id is None:
            _reject(
                rejected,
                source="interventions",
                position=position,
                reason_code="invalid_participant_id",
                detail="participant_id must be a nonempty string",
            )
            continue
        occurred_on = _iso_date(row["occurred_on"])
        if occurred_on is None:
            _reject(
                rejected,
                source="interventions",
                position=position,
                reason_code="invalid_date",
                detail="occurred_on must be an ISO calendar date",
            )
            continue
        if participant_id not in accepted_participants:
            _reject(
                rejected,
                source="interventions",
                position=position,
                reason_code="unknown_participant",
                detail="participant_id has no accepted participant row",
            )
            continue
        program_id = _nonempty_string(row["program_id"])
        if program_id is None or program_id not in accepted_programs:
            _reject(
                rejected,
                source="interventions",
                position=position,
                reason_code="unknown_program",
                detail="program_id has no accepted program row",
            )
            continue
        if (participant_id, occurred_on) not in accepted_signal_keys:
            _reject(
                rejected,
                source="interventions",
                position=position,
                reason_code="missing_participant_day",
                detail="no accepted daily signal exists for participant and date",
            )
            continue
        intervention = _nonempty_string(row["intervention"])
        if intervention is None:
            _reject(
                rejected,
                source="interventions",
                position=position,
                reason_code="invalid_intervention",
                detail="intervention must be a nonempty string",
            )
            continue
        try:
            dose_mg = normalize_dose_mg(row["dose_value"], row["dose_unit"])
        except NormalizationError as exc:
            _reject(
                rejected,
                source="interventions",
                position=position,
                reason_code=exc.reason_code,
                detail=str(exc),
            )
            continue
        accepted.append(
            {
                "intervention_id": intervention_id,
                "participant_id": participant_id,
                "program_id": program_id,
                "occurred_on": occurred_on,
                "intervention": intervention,
                "dose_mg": dose_mg,
            }
        )

    return accepted


def _participant_days(
    accepted_participants: dict[str, dict[str, str]],
    accepted_signals: list[dict[str, Any]],
    accepted_interventions: list[dict[str, Any]],
) -> pd.DataFrame:
    interventions_by_day: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for intervention in accepted_interventions:
        key = (intervention["participant_id"], intervention["occurred_on"])
        interventions_by_day.setdefault(key, []).append(intervention)

    records: list[dict[str, Any]] = []
    for signal in accepted_signals:
        key = (signal["participant_id"], signal["observed_on"])
        events = interventions_by_day.get(key, [])
        doses = [event["dose_mg"] for event in events]
        records.append(
            {
                "participant_id": signal["participant_id"],
                "observed_on": signal["observed_on"],
                "cohort": accepted_participants[signal["participant_id"]]["cohort"],
                "sleep_minutes": signal["sleep_minutes"],
                "active_minutes": signal["active_minutes"],
                "average_pulse_bpm": signal["average_pulse_bpm"],
                "intervention_event_count": len(doses),
                "distinct_program_count": len({event["program_id"] for event in events}),
                "total_intervention_dose_mg": math.fsum(doses),
                "quality_status": "accepted",
            }
        )

    participant_days = pd.DataFrame(records, columns=PARTICIPANT_DAY_COLUMNS)
    if not participant_days.empty:
        participant_days = participant_days.sort_values(
            ["participant_id", "observed_on"],
            kind="stable",
        ).reset_index(drop=True)
        participant_days["intervention_event_count"] = participant_days[
            "intervention_event_count"
        ].astype("int64")
        participant_days["distinct_program_count"] = participant_days[
            "distinct_program_count"
        ].astype("int64")
    return participant_days


def _rejected_records(rejected: list[dict[str, Any]]) -> pd.DataFrame:
    if not rejected:
        return pd.DataFrame(columns=REJECTED_COLUMNS)
    rejected_frame = pd.DataFrame(rejected)
    rejected_frame = rejected_frame.sort_values(
        ["_source_order", "_row_position"],
        kind="stable",
    )
    return rejected_frame.loc[:, REJECTED_COLUMNS].reset_index(drop=True)


def run_pipeline(
    participants: pd.DataFrame,
    programs: pd.DataFrame,
    daily_signals: pd.DataFrame,
    interventions: pd.DataFrame,
) -> PipelineResult:
    """Build curated participant-days and deterministic quality evidence."""

    participant_rows = _copy_and_require_columns(
        participants,
        "participants",
        PARTICIPANT_COLUMNS,
    )
    signal_rows = _copy_and_require_columns(
        daily_signals,
        "daily_signals",
        DAILY_SIGNAL_COLUMNS,
    )
    program_rows = _copy_and_require_columns(programs, "programs", PROGRAM_COLUMNS)
    intervention_rows = _copy_and_require_columns(
        interventions,
        "interventions",
        INTERVENTION_COLUMNS,
    )

    rejected: list[dict[str, Any]] = []
    accepted_participants = _process_participants(participant_rows, rejected)
    accepted_programs = _process_programs(program_rows, rejected)
    accepted_signals = _process_daily_signals(
        signal_rows,
        accepted_participants,
        rejected,
    )
    accepted_signal_keys = {
        (signal["participant_id"], signal["observed_on"]) for signal in accepted_signals
    }
    accepted_interventions = _process_interventions(
        intervention_rows,
        accepted_participants,
        accepted_programs,
        accepted_signal_keys,
        rejected,
    )

    participant_days = _participant_days(
        accepted_participants,
        accepted_signals,
        accepted_interventions,
    )
    rejected_records = _rejected_records(rejected)

    source_counts = {
        "participants": len(participant_rows),
        "programs": len(program_rows),
        "daily_signals": len(signal_rows),
        "interventions": len(intervention_rows),
    }
    accepted_counts = {
        "participants": len(accepted_participants),
        "programs": len(accepted_programs),
        "daily_signals": len(accepted_signals),
        "interventions": len(accepted_interventions),
    }
    rejected_counts = {
        source: int((rejected_records["source"] == source).sum()) for source in SOURCE_ORDER
    }
    duplicate_counts = {
        "participants": int((rejected_records["reason_code"] == "duplicate_participant_id").sum()),
        "programs": int((rejected_records["reason_code"] == "duplicate_program_id").sum()),
        "daily_signals": int((rejected_records["reason_code"] == "duplicate_signal_key").sum()),
        "interventions": int(
            (rejected_records["reason_code"] == "duplicate_intervention_id").sum()
        ),
    }
    missing_participant_counts = {
        source: int(
            (
                (rejected_records["source"] == source)
                & (rejected_records["reason_code"] == "unknown_participant")
            ).sum()
        )
        for source in ("daily_signals", "interventions")
    }
    audit: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "source_counts": source_counts,
        "accepted_counts": accepted_counts,
        "rejected_counts": rejected_counts,
        "output_count": len(participant_days),
        "duplicate_counts": duplicate_counts,
        "missing_participant_counts": missing_participant_counts,
        "source_profiles": {
            source: asdict(profile)
            for source, profile in _build_source_profiles(
                {
                    "participants": (participant_rows, PARTICIPANT_COLUMNS, "participant_id"),
                    "programs": (program_rows, PROGRAM_COLUMNS, "program_id"),
                    "daily_signals": (
                        signal_rows,
                        DAILY_SIGNAL_COLUMNS,
                        ("participant_id", "observed_on"),
                    ),
                    "interventions": (
                        intervention_rows,
                        INTERVENTION_COLUMNS,
                        "intervention_id",
                    ),
                },
                accepted_counts,
                rejected_counts,
            ).items()
        },
        "content_hashes": {
            "participant_days": _canonical_hash(participant_days),
            "rejected_records": _canonical_hash(rejected_records),
        },
    }

    return PipelineResult(
        participant_days=participant_days,
        rejected_records=rejected_records,
        audit=audit,
    )


def _build_source_profiles(
    sources: dict[str, tuple[pd.DataFrame, tuple[str, ...], str | tuple[str, ...]]],
    accepted_counts: dict[str, int],
    rejected_counts: dict[str, int],
) -> dict[str, SourceProfile]:
    """Return bounded aggregate metadata without source values."""
    profiles: dict[str, SourceProfile] = {}
    for source, (frame, required_columns, key_columns) in sources.items():
        keys = [key_columns] if isinstance(key_columns, str) else list(key_columns)
        profiles[source] = SourceProfile(
            row_count=len(frame),
            column_count=len(frame.columns),
            required_field_null_counts={
                column: int(frame[column].isna().sum()) for column in required_columns
            },
            duplicate_key_count=int(frame.duplicated(keys, keep=False).sum()),
            accepted_count=accepted_counts[source],
            rejected_count=rejected_counts[source],
        )
    return profiles


def profile_sources(
    participants: pd.DataFrame,
    programs: pd.DataFrame,
    daily_signals: pd.DataFrame,
    interventions: pd.DataFrame,
) -> dict[str, SourceProfile]:
    """Validate all sources and return their aggregate processing profiles."""
    result = run_pipeline(participants, programs, daily_signals, interventions)
    return {
        source: SourceProfile(**profile)
        for source, profile in result.audit["source_profiles"].items()
    }


def audit_to_json(result: PipelineResult) -> str:
    """Serialize audit evidence using canonical JSON ordering."""

    return json.dumps(
        result.audit,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
