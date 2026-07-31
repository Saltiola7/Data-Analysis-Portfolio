"""Domain records for content classification evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline


@dataclass(frozen=True)
class ContentFixture:
    """Deterministic synthetic content observations."""

    frame: pd.DataFrame
    seed: int
    rows: int
    fixture_version: str
    fixture_hash: str


@dataclass(frozen=True)
class ModelArtifact:
    """Fitted model plus separated tuning/reporting inputs and lineage."""

    pipeline: Pipeline
    feature_columns: tuple[str, ...]
    seed: int
    fixture_version: str
    fixture_hash: str
    source_hash: str
    split_identity: str
    model_hash: str
    train_ids: tuple[str, ...]
    validation_ids: tuple[str, ...]
    test_ids: tuple[str, ...]
    validation_features: pd.DataFrame
    validation_targets: np.ndarray
    validation_slices: pd.DataFrame
    validation_probabilities: np.ndarray
    test_features: pd.DataFrame
    test_targets: np.ndarray
    test_slices: pd.DataFrame
    test_probabilities: np.ndarray
    baseline_class: int
    validation_baseline_accuracy: float
    test_baseline_accuracy: float
    selected_threshold: float
    threshold_selection_metric: str
    model_parameters: dict[str, Any]


@dataclass(frozen=True)
class EvaluationResult:
    """Threshold-specific decisions and aggregate evidence for one partition."""

    partition: str
    threshold: float
    model_hash: str
    split_identity: str
    probability_hash: str
    metrics: dict[str, float | int]
    predictions: pd.DataFrame
    slices: pd.DataFrame
    calibration: pd.DataFrame


@dataclass(frozen=True)
class BootstrapInterval:
    """Reserved-test precision estimate and deterministic percentile interval."""

    point_estimate: float
    lower: float
    upper: float
    confidence: float
    resamples: int
    seed: int
