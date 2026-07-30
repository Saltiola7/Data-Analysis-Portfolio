"""Leakage-safe deterministic model training and threshold selection."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .contracts import (
    CATEGORICAL_FEATURES,
    FEATURE_ALLOWLIST,
    IDENTIFIER_COLUMN,
    NUMERIC_FEATURES,
    TARGET_COLUMN,
    validate_training_frame,
)
from .hashing import hash_frame, hash_mapping, hash_strings
from .models import ModelArtifact

TEST_SIZE = 0.20
VALIDATION_SIZE_OF_REMAINDER = 0.25
VALIDATION_SIZE = 0.20
THRESHOLD_GRID = tuple(round(value, 2) for value in np.linspace(0.10, 0.90, 17))
THRESHOLD_SELECTION_METRIC = "validation_f1_then_balanced_accuracy"
SYNTHETIC_FIXTURE_VERSION = "content-performance-synthetic-v1"
USER_FIXTURE_VERSION = "user-supplied-v1"


def train_classifier(frame: pd.DataFrame, *, seed: int = 2026) -> ModelArtifact:
    """Fit one classifier and reserve test data from threshold development."""
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")

    fixture_version = (
        SYNTHETIC_FIXTURE_VERSION
        if frame.attrs.get("fixture_version") == SYNTHETIC_FIXTURE_VERSION
        else USER_FIXTURE_VERSION
    )
    validated = validate_training_frame(frame)
    source_columns = (IDENTIFIER_COLUMN, *FEATURE_ALLOWLIST, TARGET_COLUMN)
    source_hash = hash_frame(validated.loc[:, source_columns])
    fixture_hash = source_hash

    row_positions = np.arange(len(validated))
    train_validation_positions, test_positions = train_test_split(
        row_positions,
        test_size=TEST_SIZE,
        random_state=seed,
        stratify=validated[TARGET_COLUMN],
    )
    train_positions, validation_positions = train_test_split(
        train_validation_positions,
        test_size=VALIDATION_SIZE_OF_REMAINDER,
        random_state=seed,
        stratify=validated.iloc[train_validation_positions][TARGET_COLUMN],
    )
    train_frame = validated.iloc[train_positions].reset_index(drop=True)
    validation_frame = validated.iloc[validation_positions].reset_index(drop=True)
    test_frame = validated.iloc[test_positions].reset_index(drop=True)

    preprocessing = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                list(CATEGORICAL_FEATURES),
            ),
            ("numeric", StandardScaler(), list(NUMERIC_FEATURES)),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    classifier = LogisticRegression(
        random_state=seed,
        max_iter=1_000,
        solver="liblinear",
    )
    pipeline = Pipeline(
        [
            ("preprocessing", preprocessing),
            ("classifier", classifier),
        ]
    )
    pipeline.fit(
        train_frame.loc[:, FEATURE_ALLOWLIST],
        train_frame[TARGET_COLUMN],
    )

    validation_features = validation_frame.loc[:, FEATURE_ALLOWLIST].copy(deep=True)
    validation_targets = validation_frame[TARGET_COLUMN].to_numpy(dtype="int8", copy=True)
    validation_probabilities = pipeline.predict_proba(validation_features)[:, 1].astype("float64")
    selected_threshold = _select_threshold(validation_targets, validation_probabilities)

    test_features = test_frame.loc[:, FEATURE_ALLOWLIST].copy(deep=True)
    test_targets = test_frame[TARGET_COLUMN].to_numpy(dtype="int8", copy=True)
    test_probabilities = pipeline.predict_proba(test_features)[:, 1].astype("float64")
    train_ids = tuple(train_frame[IDENTIFIER_COLUMN].astype(str))
    validation_ids = tuple(validation_frame[IDENTIFIER_COLUMN].astype(str))
    test_ids = tuple(test_frame[IDENTIFIER_COLUMN].astype(str))
    split_identity = hash_mapping(
        {
            "seed": seed,
            "test_size": TEST_SIZE,
            "validation_size": VALIDATION_SIZE,
            "train_ids": hash_strings(train_ids),
            "validation_ids": hash_strings(validation_ids),
            "test_ids": hash_strings(test_ids),
        }
    )

    class_counts = train_frame[TARGET_COLUMN].value_counts()
    baseline_class = int(class_counts.idxmax())
    validation_baseline_accuracy = float(np.mean(validation_targets == baseline_class))
    test_baseline_accuracy = float(np.mean(test_targets == baseline_class))
    model_parameters: dict[str, Any] = {
        "classifier": "sklearn.linear_model.LogisticRegression",
        "solver": classifier.solver,
        "max_iter": classifier.max_iter,
        "random_state": seed,
        "test_size": TEST_SIZE,
        "validation_size": VALIDATION_SIZE,
        "threshold_grid": list(THRESHOLD_GRID),
        "threshold_selection_metric": THRESHOLD_SELECTION_METRIC,
        "selected_threshold": selected_threshold,
        "feature_columns": list(FEATURE_ALLOWLIST),
    }
    model_hash = hash_mapping(
        {
            "lineage": model_parameters,
            "source_hash": source_hash,
            "split_identity": split_identity,
            "coefficients": classifier.coef_,
            "intercept": classifier.intercept_,
            "classes": classifier.classes_,
        }
    )
    return ModelArtifact(
        pipeline=pipeline,
        feature_columns=FEATURE_ALLOWLIST,
        seed=seed,
        fixture_version=fixture_version,
        fixture_hash=fixture_hash,
        source_hash=source_hash,
        split_identity=split_identity,
        model_hash=model_hash,
        train_ids=train_ids,
        validation_ids=validation_ids,
        test_ids=test_ids,
        validation_features=validation_features,
        validation_targets=validation_targets,
        validation_slices=validation_frame.loc[:, [*CATEGORICAL_FEATURES]].copy(deep=True),
        validation_probabilities=validation_probabilities,
        test_features=test_features,
        test_targets=test_targets,
        test_slices=test_frame.loc[:, [*CATEGORICAL_FEATURES]].copy(deep=True),
        test_probabilities=test_probabilities,
        baseline_class=baseline_class,
        validation_baseline_accuracy=validation_baseline_accuracy,
        test_baseline_accuracy=test_baseline_accuracy,
        selected_threshold=selected_threshold,
        threshold_selection_metric=THRESHOLD_SELECTION_METRIC,
        model_parameters=model_parameters,
    )


def _select_threshold(targets: np.ndarray, probabilities: np.ndarray) -> float:
    """Choose one reporting threshold from validation evidence only."""
    scored: list[tuple[float, float, float, float]] = []
    for threshold in THRESHOLD_GRID:
        predicted = (probabilities >= threshold).astype("int8")
        scored.append(
            (
                float(f1_score(targets, predicted, zero_division=0)),
                float(balanced_accuracy_score(targets, predicted)),
                -abs(threshold - 0.5),
                -threshold,
            )
        )
    best_index = max(range(len(scored)), key=scored.__getitem__)
    return THRESHOLD_GRID[best_index]
