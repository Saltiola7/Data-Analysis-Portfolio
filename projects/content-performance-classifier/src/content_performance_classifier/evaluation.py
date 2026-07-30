"""Threshold, calibration, slice, and error evidence."""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from .contracts import CATEGORICAL_FEATURES
from .hashing import hash_probabilities
from .models import EvaluationResult, ModelArtifact

CALIBRATION_BINS = 10
SMALL_SLICE_SUPPORT = 20


def evaluate_at_threshold(
    artifact: ModelArtifact,
    *,
    threshold: float = 0.5,
) -> EvaluationResult:
    """Explore a decision threshold on cached validation probabilities."""
    return _evaluate_partition(
        artifact=artifact,
        partition="validation",
        threshold=threshold,
    )


def evaluate_reserved_test(artifact: ModelArtifact) -> EvaluationResult:
    """Report reserved-test evidence once at the validation-selected threshold."""
    return _evaluate_partition(
        artifact=artifact,
        partition="reserved_test",
        threshold=artifact.selected_threshold,
    )


def _evaluate_partition(
    *,
    artifact: ModelArtifact,
    partition: Literal["validation", "reserved_test"],
    threshold: float,
) -> EvaluationResult:
    """Build immutable evaluation evidence for one named partition."""
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise ValueError("threshold must be a numeric value from 0 through 1")
    if not 0 <= float(threshold) <= 1:
        raise ValueError("threshold must be a numeric value from 0 through 1")

    if partition == "validation":
        probabilities = artifact.validation_probabilities
        actual = artifact.validation_targets
        identifiers = artifact.validation_ids
        slices = artifact.validation_slices
        baseline_accuracy = artifact.validation_baseline_accuracy
    else:
        probabilities = artifact.test_probabilities
        actual = artifact.test_targets
        identifiers = artifact.test_ids
        slices = artifact.test_slices
        baseline_accuracy = artifact.test_baseline_accuracy

    threshold_value = float(threshold)
    probability_values = probabilities.copy()
    actual_values = actual.copy()
    predicted = (probability_values >= threshold_value).astype("int8")
    tn, fp, fn, tp = confusion_matrix(actual_values, predicted, labels=[0, 1]).ravel()
    metrics: dict[str, float | int] = {
        "baseline_accuracy": baseline_accuracy,
        "accuracy": float(accuracy_score(actual_values, predicted)),
        "balanced_accuracy": float(balanced_accuracy_score(actual_values, predicted)),
        "precision": float(precision_score(actual_values, predicted, zero_division=0)),
        "recall": float(recall_score(actual_values, predicted, zero_division=0)),
        "f1": float(f1_score(actual_values, predicted, zero_division=0)),
        "roc_auc": float(roc_auc_score(actual_values, probability_values)),
        "brier_score": float(brier_score_loss(actual_values, probability_values)),
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }
    error_type = np.select(
        [
            (actual_values == 1) & (predicted == 1),
            (actual_values == 0) & (predicted == 0),
            (actual_values == 0) & (predicted == 1),
        ],
        ["true_positive", "true_negative", "false_positive"],
        default="false_negative",
    )
    predictions = pd.DataFrame(
        {
            "content_id": identifiers,
            "probability": probability_values,
            "threshold": threshold_value,
            "predicted_class": predicted,
            "actual_class": actual_values,
            "error_type": error_type,
        }
    )
    slice_evidence = _slice_evidence(slices, actual_values, predicted)
    calibration = _calibration_evidence(actual_values, probability_values)
    return EvaluationResult(
        partition=partition,
        threshold=threshold_value,
        model_hash=artifact.model_hash,
        split_identity=artifact.split_identity,
        probability_hash=hash_probabilities(probability_values),
        metrics=metrics,
        predictions=predictions,
        slices=slice_evidence,
        calibration=calibration,
    )


def _slice_evidence(
    slice_frame: pd.DataFrame,
    actual: np.ndarray,
    predicted: np.ndarray,
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for dimension in CATEGORICAL_FEATURES:
        for value in sorted(slice_frame[dimension].unique()):
            mask = slice_frame[dimension].to_numpy() == value
            slice_actual = actual[mask]
            slice_predicted = predicted[mask]
            _, false_positive, false_negative, _ = confusion_matrix(
                slice_actual,
                slice_predicted,
                labels=[0, 1],
            ).ravel()
            support = int(mask.sum())
            records.append(
                {
                    "dimension": dimension,
                    "value": value,
                    "support": support,
                    "precision": float(
                        precision_score(slice_actual, slice_predicted, zero_division=0)
                    ),
                    "recall": float(recall_score(slice_actual, slice_predicted, zero_division=0)),
                    "false_positive": int(false_positive),
                    "false_negative": int(false_negative),
                    "small_slice": support < SMALL_SLICE_SUPPORT,
                }
            )
    return pd.DataFrame.from_records(records)


def _calibration_evidence(actual: np.ndarray, probabilities: np.ndarray) -> pd.DataFrame:
    assignments = np.minimum((probabilities * CALIBRATION_BINS).astype(int), 9)
    records: list[dict[str, float | int | None]] = []
    for index in range(CALIBRATION_BINS):
        mask = assignments == index
        support = int(mask.sum())
        records.append(
            {
                "bin_lower": index / CALIBRATION_BINS,
                "bin_upper": (index + 1) / CALIBRATION_BINS,
                "support": support,
                "mean_probability": float(probabilities[mask].mean()) if support else None,
                "observed_rate": float(actual[mask].mean()) if support else None,
            }
        )
    return pd.DataFrame.from_records(records)
