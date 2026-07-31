from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from content_performance_classifier import (
    InputValidationError,
    benchmark_models,
    bootstrap_reserved_precision,
    generate_synthetic_content,
    select_threshold_for_minimum_recall,
    train_classifier,
)


def test_missing_numeric_values_are_imputed_without_mutating_source(fixture) -> None:
    frame = fixture.frame.copy(deep=True)
    frame.loc[frame.index[::17], "readability_score"] = np.nan
    frame.loc[frame.index[::23], "query_coverage"] = np.nan
    expected = frame.copy(deep=True)

    artifact = train_classifier(frame)

    pd.testing.assert_frame_equal(frame, expected)
    assert np.isfinite(artifact.validation_probabilities).all()
    assert np.isfinite(artifact.test_probabilities).all()


def test_all_missing_numeric_feature_fails_closed(fixture) -> None:
    frame = fixture.frame.copy(deep=True)
    frame["query_coverage"] = np.nan

    with pytest.raises(InputValidationError, match=r"query_coverage.*entirely missing"):
        train_classifier(frame)


def test_model_benchmark_is_deterministic_and_validation_only(fixture) -> None:
    first = benchmark_models(fixture.frame, seed=19)
    second = benchmark_models(fixture.frame, seed=19)

    pd.testing.assert_frame_equal(first, second)
    assert set(first["model"]) == {"logistic_regression", "random_forest", "prevalence_baseline"}
    assert set(first["partition"]) == {"validation"}
    assert first["split_identity"].nunique() == 1


def test_recall_constrained_threshold_is_explicit_and_frozen(fixture) -> None:
    artifact = train_classifier(fixture.frame, seed=31)

    threshold = select_threshold_for_minimum_recall(artifact, minimum_recall=0.75)

    assert 0 <= threshold <= 1
    predicted = artifact.validation_probabilities >= threshold
    recall = predicted[artifact.validation_targets == 1].mean()
    assert recall >= 0.75


@pytest.mark.parametrize("minimum_recall", [0.49, 0.96, True])
def test_recall_policy_rejects_invalid_floor(fixture, minimum_recall: object) -> None:
    artifact = train_classifier(fixture.frame)

    with pytest.raises(ValueError, match=r"0\.50 through 0\.95"):
        select_threshold_for_minimum_recall(artifact, minimum_recall=minimum_recall)


def test_reserved_precision_interval_is_deterministic_and_bounded(fixture) -> None:
    artifact = train_classifier(fixture.frame, seed=41)
    threshold = select_threshold_for_minimum_recall(artifact)

    first = bootstrap_reserved_precision(artifact, threshold, seed=17, resamples=200)
    second = bootstrap_reserved_precision(artifact, threshold, seed=17, resamples=200)

    assert first == second
    assert first.resamples == 200
    assert 0 <= first.lower <= first.point_estimate <= first.upper <= 1


def test_synthetic_fixture_has_bounded_predictor_missingness() -> None:
    frame = generate_synthetic_content(seed=61, rows=600).frame

    assert frame["readability_score"].isna().any()
    assert frame["query_coverage"].isna().any()
    assert not frame.loc[:, ["topic_family", "content_type", "high_engagement"]].isna().any().any()
