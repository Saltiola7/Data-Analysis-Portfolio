"""Leakage-safe deterministic model training and threshold selection."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, f1_score, precision_score, recall_score
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
from .imputation import TopicMedianImputer
from .models import ModelArtifact

TEST_SIZE = 0.20
VALIDATION_SIZE_OF_REMAINDER = 0.25
VALIDATION_SIZE = 0.20
THRESHOLD_GRID = tuple(round(value, 2) for value in np.linspace(0.10, 0.90, 17))
THRESHOLD_SELECTION_METRIC = "validation_f1_then_balanced_accuracy"
SYNTHETIC_FIXTURE_VERSION = "content-performance-synthetic-v1"
USER_FIXTURE_VERSION = "user-supplied-v1"
BENCHMARK_THRESHOLD = 0.5
MINIMUM_RECALL_FLOOR = 0.50
MAXIMUM_RECALL_FLOOR = 0.95


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
            ("imputation", TopicMedianImputer()),
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


def benchmark_models(frame: pd.DataFrame, *, seed: int = 2026) -> pd.DataFrame:
    """Compare fixed models on one validation partition; never inspect reserved test."""
    artifact = train_classifier(frame, seed=seed)
    validated = validate_training_frame(frame)
    by_id = validated.set_index(IDENTIFIER_COLUMN)
    train_frame = by_id.loc[list(artifact.train_ids)].reset_index()
    validation_frame = by_id.loc[list(artifact.validation_ids)].reset_index()
    validation_targets = artifact.validation_targets

    models: list[tuple[str, object | None]] = [
        ("logistic_regression", None),
        (
            "random_forest",
            RandomForestClassifier(
                n_estimators=200,
                max_depth=8,
                min_samples_leaf=3,
                random_state=seed,
                n_jobs=1,
            ),
        ),
        ("prevalence_baseline", None),
    ]
    records: list[dict[str, object]] = []
    for name, classifier in models:
        if name == "logistic_regression":
            probabilities = artifact.validation_probabilities
        elif name == "prevalence_baseline":
            probabilities = np.full(
                len(validation_frame),
                float(train_frame[TARGET_COLUMN].mean()),
            )
        else:
            pipeline = Pipeline(
                [
                    ("imputation", TopicMedianImputer()),
                    (
                        "preprocessing",
                        ColumnTransformer(
                            [
                                (
                                    "categorical",
                                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                                    list(CATEGORICAL_FEATURES),
                                ),
                                ("numeric", StandardScaler(), list(NUMERIC_FEATURES)),
                            ],
                            verbose_feature_names_out=False,
                        ),
                    ),
                    ("classifier", classifier),
                ]
            )
            pipeline.fit(train_frame.loc[:, FEATURE_ALLOWLIST], train_frame[TARGET_COLUMN])
            probabilities = pipeline.predict_proba(validation_frame.loc[:, FEATURE_ALLOWLIST])[
                :, 1
            ]
        predicted = (probabilities >= BENCHMARK_THRESHOLD).astype("int8")
        records.append(
            {
                "model": name,
                "partition": "validation",
                "split_identity": artifact.split_identity,
                "precision": float(
                    precision_score(validation_targets, predicted, zero_division=0)
                ),
                "recall": float(recall_score(validation_targets, predicted, zero_division=0)),
                "f1": float(f1_score(validation_targets, predicted, zero_division=0)),
                "balanced_accuracy": float(balanced_accuracy_score(validation_targets, predicted)),
            }
        )
    return pd.DataFrame.from_records(records)


def select_threshold_for_minimum_recall(
    artifact: ModelArtifact,
    *,
    minimum_recall: float = 0.75,
) -> float:
    """Maximize validation precision subject to an explicit recall floor."""
    if (
        isinstance(minimum_recall, bool)
        or not isinstance(minimum_recall, (int, float))
        or not MINIMUM_RECALL_FLOOR <= float(minimum_recall) <= MAXIMUM_RECALL_FLOOR
    ):
        raise ValueError("minimum_recall must be numeric from 0.50 through 0.95")
    candidates = sorted({0.0, 1.0, *(float(value) for value in artifact.validation_probabilities)})
    feasible: list[tuple[float, float, float]] = []
    for threshold in candidates:
        predicted = (artifact.validation_probabilities >= threshold).astype("int8")
        recall = float(recall_score(artifact.validation_targets, predicted, zero_division=0))
        if recall >= float(minimum_recall):
            precision = float(
                precision_score(artifact.validation_targets, predicted, zero_division=0)
            )
            feasible.append((precision, recall, threshold))
    if not feasible:
        raise ValueError(
            "no validation threshold satisfies the minimum recall; lower the recall floor"
        )
    return max(feasible)[2]


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
