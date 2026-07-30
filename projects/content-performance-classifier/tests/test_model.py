from __future__ import annotations

import json

import numpy as np
import pandas as pd

from content_performance_classifier import (
    audit_to_json,
    evaluate_at_threshold,
    evaluate_reserved_test,
    train_classifier,
)


def test_train_validation_test_split_and_probabilities_are_stable(fixture) -> None:
    first = train_classifier(fixture.frame, seed=73)
    second = train_classifier(fixture.frame, seed=73)

    assert first.split_identity == second.split_identity
    assert first.model_hash == second.model_hash
    np.testing.assert_allclose(
        first.validation_probabilities,
        second.validation_probabilities,
    )
    np.testing.assert_allclose(first.test_probabilities, second.test_probabilities)
    assert first.train_ids == second.train_ids
    assert first.validation_ids == second.validation_ids
    assert first.test_ids == second.test_ids
    assert set(first.train_ids).isdisjoint(first.validation_ids)
    assert set(first.train_ids).isdisjoint(first.test_ids)
    assert set(first.validation_ids).isdisjoint(first.test_ids)


def test_model_and_baseline_use_same_validation_split_during_threshold_exploration(
    artifact,
) -> None:
    result = evaluate_at_threshold(artifact, threshold=0.5)
    required_metrics = {
        "baseline_accuracy",
        "accuracy",
        "balanced_accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "brier_score",
        "true_negative",
        "false_positive",
        "false_negative",
        "true_positive",
    }

    assert required_metrics <= result.metrics.keys()
    assert result.metrics["accuracy"] >= result.metrics["baseline_accuracy"]
    assert result.metrics["roc_auc"] > 0.7
    assert len(result.predictions) == len(artifact.validation_ids)
    assert result.predictions["content_id"].tolist() == list(artifact.validation_ids)
    assert result.predictions["actual_class"].tolist() == artifact.validation_targets.tolist()
    assert sum(
        result.metrics[name]
        for name in ("true_negative", "false_positive", "false_negative", "true_positive")
    ) == len(result.predictions)


def test_threshold_exploration_changes_validation_not_reserved_test(artifact) -> None:
    low = evaluate_at_threshold(artifact, threshold=0.3)
    high = evaluate_at_threshold(artifact, threshold=0.7)
    reserved_before = evaluate_reserved_test(artifact)
    reserved_after = evaluate_reserved_test(artifact)

    assert low.partition == high.partition == "validation"
    assert reserved_before.partition == reserved_after.partition == "reserved_test"
    assert low.model_hash == high.model_hash == artifact.model_hash
    assert low.split_identity == high.split_identity == artifact.split_identity
    assert low.probability_hash == high.probability_hash
    np.testing.assert_allclose(
        low.predictions["probability"],
        high.predictions["probability"],
    )
    assert low.predictions["predicted_class"].sum() >= high.predictions["predicted_class"].sum()
    assert reserved_before.threshold == reserved_after.threshold == artifact.selected_threshold
    assert reserved_before.probability_hash == reserved_after.probability_hash
    pd.testing.assert_frame_equal(
        reserved_before.predictions,
        reserved_after.predictions,
    )
    assert reserved_before.predictions["content_id"].tolist() == list(artifact.test_ids)


def test_calibration_and_slice_evidence_are_complete(artifact) -> None:
    result = evaluate_at_threshold(artifact)

    assert {
        "bin_lower",
        "bin_upper",
        "support",
        "mean_probability",
        "observed_rate",
    } <= set(result.calibration.columns)
    assert result.calibration["support"].sum() == len(result.predictions)

    assert {
        "dimension",
        "value",
        "support",
        "precision",
        "recall",
        "false_positive",
        "false_negative",
        "small_slice",
    } <= set(result.slices.columns)
    for dimension in ("topic_family", "content_type"):
        dimension_rows = result.slices.loc[result.slices["dimension"] == dimension]
        assert dimension_rows["support"].sum() == len(result.predictions)
    assert result.slices["small_slice"].dtype == bool


def test_audit_is_metadata_only_and_serializable(artifact) -> None:
    result = evaluate_at_threshold(artifact, threshold=0.42)
    audit_text = audit_to_json(artifact, result)
    audit = json.loads(audit_text)

    assert audit["fixture"]["version"]
    assert audit["training"]["split_identity"] == artifact.split_identity
    assert audit["evaluation"]["threshold"] == 0.42
    assert audit["evaluation"]["probability_hash"] == result.probability_hash
    assert "content-000001" not in audit_text
    assert "credential" not in audit_text.lower()
    assert "password" not in audit_text.lower()
    assert "NaN" not in audit_text


def test_metadata_audit_never_discloses_uploaded_category_labels(fixture) -> None:
    frame = fixture.frame.copy(deep=True)
    frame["topic_family"] = np.where(
        frame.index % 2 == 0,
        "private-client-alpha",
        "private-client-beta",
    )
    frame["content_type"] = np.where(
        frame.index % 3 == 0,
        "secret-campaign-one",
        "secret-campaign-two",
    )
    artifact = train_classifier(frame)
    result = evaluate_at_threshold(artifact)

    audit_text = audit_to_json(artifact, result)
    audit = json.loads(audit_text)

    for sensitive_label in (
        "private-client-alpha",
        "private-client-beta",
        "secret-campaign-one",
        "secret-campaign-two",
    ):
        assert sensitive_label not in audit_text
    assert all(
        row["value"].startswith("category-") for row in audit["evaluation"]["validation_slices"]
    )


def test_error_types_match_actual_and_predicted_classes(artifact) -> None:
    result = evaluate_at_threshold(artifact)
    predictions = result.predictions
    expected = np.select(
        [
            (predictions["actual_class"] == 1) & (predictions["predicted_class"] == 1),
            (predictions["actual_class"] == 0) & (predictions["predicted_class"] == 0),
            (predictions["actual_class"] == 0) & (predictions["predicted_class"] == 1),
        ],
        ["true_positive", "true_negative", "false_positive"],
        default="false_negative",
    )

    pd.testing.assert_series_equal(
        predictions["error_type"],
        pd.Series(expected, name="error_type"),
    )
