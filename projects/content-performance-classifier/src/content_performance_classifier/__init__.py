"""Leakage-aware synthetic content classification."""

from .contracts import (
    CONTENT_COLUMNS,
    CONTENT_TYPES,
    FEATURE_ALLOWLIST,
    TOPIC_FAMILIES,
    InputValidationError,
)
from .evaluation import evaluate_at_threshold, evaluate_reserved_test
from .exports import audit_to_json, predictions_to_safe_csv
from .models import ContentFixture, EvaluationResult, ModelArtifact
from .synthetic import FIXTURE_VERSION, generate_synthetic_content
from .training import train_classifier
from .uploads import read_content_csv

__all__ = [
    "CONTENT_COLUMNS",
    "CONTENT_TYPES",
    "FEATURE_ALLOWLIST",
    "FIXTURE_VERSION",
    "TOPIC_FAMILIES",
    "ContentFixture",
    "EvaluationResult",
    "InputValidationError",
    "ModelArtifact",
    "audit_to_json",
    "evaluate_at_threshold",
    "evaluate_reserved_test",
    "generate_synthetic_content",
    "predictions_to_safe_csv",
    "read_content_csv",
    "train_classifier",
]
