---
title: Content Performance Classifier
status: approved
type: flagship-project
version: 1.0
last_updated: 2026-07-29
bounded_context: content_performance_classifier
risk: routine
---

# Content Performance Classifier

## Goal

Demonstrate leakage-aware, reproducible data-science work through a synthetic
content-performance classification problem. The project must expose baseline,
model, threshold, calibration, slice, and error evidence without using employer
features, labels, taxonomies, thresholds, data, or metrics.

## Domain

`ContentObservation` has one row per synthetic content item:

- stable content identifier
- topic family
- content type
- word count
- readability score
- age in days
- internal-link count
- entity count
- query coverage
- update cadence
- binary `high_engagement` label

`TrainingRun` records fixture version, seed, feature contract, split identity,
model parameters, metrics, and deterministic content hashes.

`Prediction` records content identity, probability, threshold, predicted class,
actual class when available, and error type.

## Behavior

### Generate reproducible synthetic evidence

Given a seed and row count, when the fixture is generated, then schema, values,
labels, row order, and fixture identity are reproducible. Labels arise from a
documented independent synthetic mechanism with bounded noise.

### Compare against a baseline

Given a labeled training split, when evaluation runs, then the majority-class
baseline and fitted classifier are measured on the same untouched test split.

### Prevent target leakage

Given input data contains the target or prohibited proxy columns, when features
are assembled, then only the explicit feature allowlist reaches model fitting.
Identifier and split columns never become predictors.

### Tune a decision threshold without retraining

Given test probabilities, when a visitor changes the threshold, then
predictions and threshold-dependent metrics update while the fitted model,
split, and probabilities remain unchanged.

### Expose uneven performance

Given multiple topic families and content types, when evaluation runs, then
per-slice support, precision, recall, and error counts accompany aggregate
metrics. Small slices are labeled rather than overinterpreted.

### Export safe evidence

Given predictions and evaluation evidence, when export is requested, then CSV
formula strings are neutralized and the audit JSON contains no uploaded rows or
credentials.

## Interfaces

```python
def generate_synthetic_content(
    seed: int = 2026,
    rows: int = 600,
) -> ContentFixture: ...

def train_classifier(
    frame: pandas.DataFrame,
    *,
    seed: int = 2026,
) -> ModelArtifact: ...

def evaluate_at_threshold(
    artifact: ModelArtifact,
    *,
    threshold: float = 0.5,
) -> EvaluationResult: ...

def predictions_to_safe_csv(result: EvaluationResult) -> str: ...

def audit_to_json(artifact: ModelArtifact, result: EvaluationResult) -> str: ...
```

The Marimo notebook is a thin adapter over these tested functions.

## Contracts

- Training input is copied before use and limited to 5,000 rows.
- Required columns and value ranges fail closed before fitting.
- The feature allowlist is immutable and excludes identifiers, labels, outcome
  proxies, free text, and split markers.
- Train/test split is deterministic, stratified, and recorded.
- Preprocessing is fit only on the training split through one pipeline.
- A fixed-seed logistic classifier is the transparent MVP model.
- Evaluation includes baseline accuracy, accuracy, balanced accuracy,
  precision, recall, F1, ROC AUC, Brier score, confusion counts, and slice
  support.
- Undefined metrics use explicit zero-division behavior and remain visible.
- The notebook states that synthetic performance does not estimate production
  uplift or external validity.
- Uploaded data remains runtime-only; no network or persistence is used.
- No DataCamp assessment material or employer-derived feature design enters the
  repository.

## Validation

- Red tests cover determinism, schema/range failure, leakage exclusion, split
  stability, baseline comparison, threshold invariance, slice accounting,
  hashes, input immutability, and safe export.
- Focused pytest and curated Ruff checks pass.
- Strict Marimo check and executable HTML export pass.
- Privacy, provenance, and restricted-material scans pass.
