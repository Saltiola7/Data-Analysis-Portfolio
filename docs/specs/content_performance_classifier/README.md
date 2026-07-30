---
title: Content Performance Classifier
status: approved
type: flagship-project
version: 1.1
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

### Compare against a baseline without leaking partitions

Given training, validation, and reserved-test splits, when evaluation runs,
then the majority-class baseline is fit from training labels, validation
supports exploration, and reserved-test evidence uses only the
validation-selected reporting threshold.

### Prevent target leakage

Given input data contains the target or prohibited proxy columns, when features
are assembled, then only the explicit feature allowlist reaches model fitting.
Identifier and split columns never become predictors.

### Tune a decision threshold without retraining

Given cached validation probabilities, when a visitor changes the threshold,
then validation predictions and threshold-dependent metrics update while the
fitted model, split identities, probabilities, and reserved-test reporting
threshold remain unchanged.

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
- The deterministic stratified split is 60% training, 20% validation, and 20%
  reserved test, with partition identities recorded.
- Preprocessing is fit only on the training split through one pipeline.
- A fixed-seed logistic classifier is the transparent MVP model.
- Validation-only threshold exploration selects one reporting threshold.
- Reserved-test evidence uses that fixed threshold and never drives the slider
  or threshold-selection rule.
- Evaluation includes baseline accuracy, accuracy, balanced accuracy,
  precision, recall, F1, ROC AUC, Brier score, confusion counts, calibration,
  and slice support.
- Undefined metrics use explicit zero-division behavior and remain visible.
- The notebook states that synthetic performance does not estimate production
  uplift or external validity.
- Uploaded data remains runtime-only; no network or persistence is used.
- No copied DataCamp prompt, supplied dataset, solution code, exact feature
  design, label, threshold, metric, output, or credential image enters the
  repository.

## Validation

- Twenty-seven focused tests cover determinism, schema/range failure, leakage
  exclusion, three-way split stability, baseline comparison, validation-only
  threshold selection, reserved-test invariance, slice accounting, hashes,
  input immutability, and safe export.
- Focused pytest and curated Ruff checks pass.
- Strict Marimo, executed WASM package, committed-session source identity, and
  Chromium interaction gates pass.
- Privacy, provenance, and restricted-material scans pass.
