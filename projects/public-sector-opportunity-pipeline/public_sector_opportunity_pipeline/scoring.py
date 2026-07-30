"""Transparent additive fit scoring for canonical opportunities."""

from __future__ import annotations

import math
import re

import pandas as pd

from public_sector_opportunity_pipeline.errors import PipelineInputError
from public_sector_opportunity_pipeline.models import FitPreferences
from public_sector_opportunity_pipeline.normalization import (
    CANONICAL_COLUMNS,
    SUPPORTED_ENGAGEMENTS,
)

_TAG_PUNCTUATION = re.compile(r"[^a-z0-9]+")
CONTRIBUTION_COLUMNS = [
    "skill_contribution",
    "engagement_contribution",
    "location_contribution",
    "value_contribution",
]
MAX_PREFERENCE_ITEMS = 100
MAX_PREFERENCE_TEXT_LENGTH = 128


def score_opportunities(
    opportunities: pd.DataFrame,
    preferences: FitPreferences,
) -> pd.DataFrame:
    """Add visible rule contributions and a non-probabilistic total."""

    missing = [column for column in CANONICAL_COLUMNS if column not in opportunities]
    if missing:
        raise PipelineInputError(
            "canonical opportunities are missing required scoring fields"
        )
    normalized_preferences = _normalize_preferences(preferences)
    scored = opportunities.loc[:, CANONICAL_COLUMNS].copy(deep=True)
    contribution_rows: list[dict[str, object]] = []

    for row in scored.to_dict("records"):
        row_tags = set(str(row["skill_tags"]).split("|"))
        matched = tuple(
            sorted(row_tags.intersection(normalized_preferences.skill_tags))
        )
        skill_contribution = min(4.0, 2.0 * len(matched))
        engagement_contribution = (
            2.0
            if row["engagement_type"] in normalized_preferences.engagement_types
            else 0.0
        )
        location_contribution = (
            1.0
            if normalized_preferences.remote_preferred
            and row["location_policy"] in {"remote", "flexible"}
            else 0.0
        )
        value_contribution = (
            1.0
            if normalized_preferences.minimum_value_usd is not None
            and float(row["value_max_usd"]) >= normalized_preferences.minimum_value_usd
            else 0.0
        )
        fit_score = (
            skill_contribution
            + engagement_contribution
            + location_contribution
            + value_contribution
        )
        contribution_rows.append(
            {
                "matched_skills": "|".join(matched),
                "skill_contribution": skill_contribution,
                "engagement_contribution": engagement_contribution,
                "location_contribution": location_contribution,
                "value_contribution": value_contribution,
                "fit_score": fit_score,
                "score_explanation": (
                    f"Rule total {fit_score:.1f}: skills "
                    f"{skill_contribution:.1f}, engagement "
                    f"{engagement_contribution:.1f}, location "
                    f"{location_contribution:.1f}, value "
                    f"{value_contribution:.1f}."
                ),
            }
        )

    contributions = pd.DataFrame(
        contribution_rows,
        index=scored.index,
        columns=[
            "matched_skills",
            *CONTRIBUTION_COLUMNS,
            "fit_score",
            "score_explanation",
        ],
    )
    scored = pd.concat([scored, contributions], axis=1)
    return scored.sort_values(
        ["fit_score", "canonical_id"],
        ascending=[False, True],
        kind="stable",
    ).reset_index(drop=True)


def _normalize_preferences(preferences: FitPreferences) -> FitPreferences:
    if not isinstance(preferences, FitPreferences):
        raise PipelineInputError("fit preferences must use FitPreferences")
    _validate_preference_items(preferences.skill_tags, "skill tags")
    _validate_preference_items(
        preferences.engagement_types,
        "engagement types",
    )
    tags = tuple(
        sorted(
            {
                _TAG_PUNCTUATION.sub("-", tag.casefold()).strip("-")
                for tag in preferences.skill_tags
            }
        )
    )
    if any(not tag for tag in tags):
        raise PipelineInputError("fit preferences contain an invalid skill tag")
    engagements = tuple(
        sorted({engagement.casefold() for engagement in preferences.engagement_types})
    )
    if set(engagements) - set(SUPPORTED_ENGAGEMENTS):
        raise PipelineInputError("fit preferences contain unsupported engagement")
    if not isinstance(preferences.remote_preferred, bool):
        raise PipelineInputError("fit preferences remote flag must be boolean")
    minimum = preferences.minimum_value_usd
    if minimum is not None and (
        isinstance(minimum, bool)
        or not isinstance(minimum, (int, float))
        or minimum < 0
        or not math.isfinite(float(minimum))
    ):
        raise PipelineInputError("minimum opportunity value must be non-negative")
    return FitPreferences(
        skill_tags=tags,
        engagement_types=engagements,
        remote_preferred=preferences.remote_preferred,
        minimum_value_usd=float(minimum) if minimum is not None else None,
    )


def _validate_preference_items(value: object, field: str) -> None:
    if not isinstance(value, tuple) or len(value) > MAX_PREFERENCE_ITEMS:
        raise PipelineInputError(
            f"fit preferences {field} must be a tuple of at most "
            f"{MAX_PREFERENCE_ITEMS} strings"
        )
    if any(
        not isinstance(item, str)
        or not item.strip()
        or len(item) > MAX_PREFERENCE_TEXT_LENGTH
        for item in value
    ):
        raise PipelineInputError(
            f"fit preferences {field} must contain bounded nonempty strings"
        )
