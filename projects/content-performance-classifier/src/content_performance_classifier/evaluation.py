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
from .models import BootstrapInterval, EvaluationResult, ModelArtifact

CALIBRATION_BINS = 10
SMALL_SLICE_SUPPORT = 20
MIN_BOOTSTRAP_RESAMPLES = 100
MAX_BOOTSTRAP_RESAMPLES = 5_000


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


def evaluate_reserved_test(
    artifact: ModelArtifact,
    *,
    threshold: float | None = None,
) -> EvaluationResult:
    """Report reserved-test evidence once at the validation-selected threshold."""
    return _evaluate_partition(
        artifact=artifact,
        partition="reserved_test",
        threshold=artifact.selected_threshold if threshold is None else threshold,
    )


def bootstrap_reserved_precision(
    artifact: ModelArtifact,
    threshold: float,
    *,
    seed: int = 2026,
    resamples: int = 500,
) -> BootstrapInterval:
    """Estimate reserved-test precision uncertainty without threshold retuning."""
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if (
        isinstance(resamples, bool)
        or not isinstance(resamples, int)
        or not MIN_BOOTSTRAP_RESAMPLES <= resamples <= MAX_BOOTSTRAP_RESAMPLES
    ):
        raise ValueError("resamples must be an integer from 100 through 5,000")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise ValueError("threshold must be a numeric value from 0 through 1")
    threshold_value = float(threshold)
    if not 0 <= threshold_value <= 1:
        raise ValueError("threshold must be a numeric value from 0 through 1")

    targets = artifact.test_targets
    classes = {int(value) for value in np.unique(targets)}
    if classes != {0, 1}:
        raise ValueError("reserved test must contain both classes for stratified bootstrap")
    probabilities = artifact.test_probabilities
    predicted = (probabilities >= threshold_value).astype("int8")
    point_estimate = float(precision_score(targets, predicted, zero_division=0))
    rng = np.random.default_rng(seed)
    class_indices = [np.flatnonzero(targets == value) for value in (0, 1)]
    estimates = np.empty(resamples, dtype="float64")
    for index in range(resamples):
        sampled = np.concatenate(
            [rng.choice(indices, size=len(indices), replace=True) for indices in class_indices]
        )
        estimates[index] = precision_score(
            targets[sampled],
            predicted[sampled],
            zero_division=0,
        )
    lower, upper = np.percentile(estimates, [2.5, 97.5])
    return BootstrapInterval(
        point_estimate=point_estimate,
        lower=float(lower),
        upper=float(upper),
        confidence=0.95,
        resamples=resamples,
        seed=seed,
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
