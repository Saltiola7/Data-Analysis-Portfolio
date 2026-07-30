from __future__ import annotations

import csv
import io
import math

import pandas as pd
import pytest

from public_sector_opportunity_pipeline import (
    FitPreferences,
    PipelineInputError,
    dataframe_to_safe_csv,
    run_pipeline,
    score_opportunities,
)

from .test_pipeline import federal_record, municipal_record


def test_fit_score_is_sum_of_visible_rule_contributions() -> None:
    opportunities = run_pipeline(
        {
            "federal": [federal_record()],
            "municipal": [municipal_record()],
        }
    ).opportunities
    preferences = FitPreferences(
        skill_tags=("python", "gcp"),
        engagement_types=("contract",),
        remote_preferred=True,
        minimum_value_usd=200_000,
    )

    scored = score_opportunities(opportunities, preferences)
    contribution_columns = [
        "skill_contribution",
        "engagement_contribution",
        "location_contribution",
        "value_contribution",
    ]

    assert (
        scored["fit_score"].tolist()
        == scored[contribution_columns].sum(axis=1).tolist()
    )
    federal = scored.loc[scored["canonical_id"] == "federal:FED-001"].iloc[0]
    assert federal["matched_skills"] == "gcp|python"
    assert federal["skill_contribution"] == 4.0
    assert federal["engagement_contribution"] == 2.0
    assert federal["location_contribution"] == 1.0
    assert federal["value_contribution"] == 1.0
    assert federal["fit_score"] == 8.0
    assert "probability" not in federal["score_explanation"].lower()


def test_scoring_is_deterministic_and_preserves_canonical_order() -> None:
    opportunities = run_pipeline(
        {
            "federal": [federal_record()],
            "municipal": [municipal_record()],
        }
    ).opportunities
    preferences = FitPreferences(skill_tags=("python",))

    first = score_opportunities(opportunities, preferences)
    second = score_opportunities(opportunities.sample(frac=1), preferences)

    assert first.to_dict("records") == second.to_dict("records")


def test_safe_csv_neutralizes_formula_prefixes_without_changing_numbers() -> None:
    frame = pd.DataFrame(
        {
            "text": [
                "=1+1",
                "+cmd",
                "-formula",
                "@lookup",
                "\tformula",
                "  =hidden",
                "\n@hidden",
                "  safe",
            ],
            "number": [-10, 2, 3, 4, 5, 6, 7, 8],
        }
    )

    exported = dataframe_to_safe_csv(frame)
    rows = list(csv.DictReader(io.StringIO(exported)))

    assert [row["text"] for row in rows] == [
        "'=1+1",
        "'+cmd",
        "'-formula",
        "'@lookup",
        "'\tformula",
        "'  =hidden",
        "'\n@hidden",
        "  safe",
    ]
    assert rows[0]["number"] == "-10"


def test_scoring_rejects_non_finite_minimum_value() -> None:
    opportunities = run_pipeline(
        {"federal": [federal_record()], "municipal": []}
    ).opportunities

    with pytest.raises(PipelineInputError, match="non-negative"):
        score_opportunities(
            opportunities,
            FitPreferences(minimum_value_usd=math.inf),
        )


@pytest.mark.parametrize(
    "preferences",
    [
        FitPreferences(skill_tags="python"),  # type: ignore[arg-type]
        FitPreferences(skill_tags=("python", 7)),  # type: ignore[arg-type]
        FitPreferences(skill_tags=(" ",)),
        FitPreferences(engagement_types=("contract", None)),  # type: ignore[arg-type]
        FitPreferences(remote_preferred=1),  # type: ignore[arg-type]
        FitPreferences(skill_tags=("x" * 129,)),
    ],
)
def test_scoring_preferences_fail_closed_on_invalid_types_and_values(
    preferences: FitPreferences,
) -> None:
    opportunities = run_pipeline(
        {"federal": [federal_record()], "municipal": []}
    ).opportunities

    with pytest.raises(PipelineInputError, match="fit preferences"):
        score_opportunities(opportunities, preferences)
