"""Leakage-aware synthetic content classification."""

from .contracts import (
    CONTENT_COLUMNS,
    CONTENT_TYPES,
    FEATURE_ALLOWLIST,
    TOPIC_FAMILIES,
    InputValidationError,
)
from .evaluation import (
    bootstrap_reserved_precision,
    evaluate_at_threshold,
    evaluate_reserved_test,
)
from .exports import audit_to_json, predictions_to_safe_csv
from .models import BootstrapInterval, ContentFixture, EvaluationResult, ModelArtifact
from .synthetic import FIXTURE_VERSION, generate_synthetic_content
from .training import (
    benchmark_models,
    select_threshold_for_minimum_recall,
    train_classifier,
)
from .uploads import read_content_csv

__all__ = [
    "CONTENT_COLUMNS",
    "CONTENT_TYPES",
    "FEATURE_ALLOWLIST",
    "FIXTURE_VERSION",
    "TOPIC_FAMILIES",
    "BootstrapInterval",
    "ContentFixture",
    "EvaluationResult",
    "InputValidationError",
    "ModelArtifact",
    "audit_to_json",
    "benchmark_models",
    "bootstrap_reserved_precision",
    "evaluate_at_threshold",
    "evaluate_reserved_test",
    "generate_synthetic_content",
    "predictions_to_safe_csv",
    "read_content_csv",
    "select_threshold_for_minimum_recall",
    "train_classifier",
]
