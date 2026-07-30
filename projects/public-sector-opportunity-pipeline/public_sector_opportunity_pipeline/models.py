"""Domain values for the public-sector opportunity pipeline."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class SourceFixture:
    """Versioned, deterministic in-memory source batches."""

    version: str
    seed: int
    batches: Mapping[str, Sequence[Mapping[str, object]]]

    def __post_init__(self) -> None:
        copied = {
            source: tuple(dict(record) for record in records)
            for source, records in self.batches.items()
        }
        object.__setattr__(self, "batches", copied)


@dataclass(frozen=True)
class PipelineState:
    """Latest accepted source-update watermark for each source."""

    schema_version: str = "1.0"
    watermarks: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "watermarks", dict(self.watermarks))


@dataclass(frozen=True)
class RunManifest:
    """Auditable facts and hashes for one deterministic run."""

    schema_version: str
    fixture_version: str
    seed: int | None
    input_count: int
    accepted_count: int
    rejected_count: int
    stale_count: int
    output_count: int
    retry_counts: Mapping[str, int]
    state_before: Mapping[str, str]
    state_after: Mapping[str, str]
    output_grain: str
    canonical_hash: str
    rejection_hash: str
    state_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "retry_counts", dict(self.retry_counts))
        object.__setattr__(self, "state_before", dict(self.state_before))
        object.__setattr__(self, "state_after", dict(self.state_after))

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable manifest."""

        return {
            "schema_version": self.schema_version,
            "fixture_version": self.fixture_version,
            "seed": self.seed,
            "input_count": self.input_count,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "stale_count": self.stale_count,
            "output_count": self.output_count,
            "retry_counts": dict(self.retry_counts),
            "state_before": dict(self.state_before),
            "state_after": dict(self.state_after),
            "output_grain": self.output_grain,
            "canonical_hash": self.canonical_hash,
            "rejection_hash": self.rejection_hash,
            "state_hash": self.state_hash,
        }


@dataclass(frozen=True)
class PipelineResult:
    """Canonical output, dead letters, control state, and audit manifest."""

    opportunities: pd.DataFrame
    rejected: pd.DataFrame
    state: PipelineState
    manifest: RunManifest


@dataclass(frozen=True)
class FitPreferences:
    """Explicit additive fit-scoring preferences."""

    skill_tags: tuple[str, ...] = ()
    engagement_types: tuple[str, ...] = ()
    remote_preferred: bool = False
    minimum_value_usd: float | None = None


@dataclass(frozen=True)
class RetryPolicy:
    """Bounded source retry attempts and injected delays."""

    max_attempts: int = 3
    delays: tuple[float, ...] = (0.0, 0.0)


@dataclass(frozen=True)
class FetchResult:
    """Validated records plus observable retry count."""

    records: tuple[Mapping[str, object], ...]
    retry_count: int
