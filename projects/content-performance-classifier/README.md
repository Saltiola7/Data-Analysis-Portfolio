# Content Performance Classifier

Leakage-aware data-science demonstration using only deterministic synthetic
content observations. A transparent logistic classifier is compared with a
majority-class baseline through a deterministic train/validation/test design.
Threshold exploration uses validation data. One validation-selected threshold
produces separately labeled reserved-test evidence.

## What it demonstrates

- explicit one-row-per-content-item schema and immutable feature allowlist
- deterministic, stratified train/validation/test splitting with recorded
  identities
- preprocessing fitted only on the training split through one sklearn pipeline
- majority-class baseline and transparent logistic-regression model
- threshold exploration over cached validation probabilities without retraining
- reserved-test reporting at one threshold selected from validation F1,
  balanced accuracy, and a deterministic tie-break
- accuracy, balanced accuracy, precision, recall, F1, ROC AUC, Brier score,
  confusion counts, calibration bins, and per-slice evidence
- metadata-only audit JSON with non-reversible category pseudonyms and
  formula-safe validation-prediction CSV exports
- bounded runtime-only CSV upload in a thin Marimo app

## Feature contract

The target is `high_engagement`. Only these predictors reach model fitting:

| Category | Features |
|---|---|
| Categorical | `topic_family`, `content_type` |
| Numeric | `word_count`, `readability_score`, `age_days`, `internal_link_count`, `entity_count`, `query_coverage`, `update_cadence` |

`content_id`, target values, free text, outcome proxies, and split markers are
excluded from the predictor boundary. Extra upload columns are ignored.

## Run locally

```bash
uv sync --locked
uv run pytest -q
uv run marimo edit src/app.py
```

Default data uses generator version `content-performance-synthetic-v1`, seed
`2026`, and 600 fictional rows. Optional uploads must be strict UTF-8 labeled
CSV files no larger than 5 MB or 5,000 rows. Uploads remain in the active
notebook runtime. Classification code does not transmit or persist upload
content, though a hosted notebook runtime may process it remotely and any
runtime may fetch application dependencies. Use the WASM export for
browser-only processing. See [PRIVACY.md](PRIVACY.md).

## Evaluation design

The deterministic split is 60% training, 20% validation, and 20% reserved
test. Preprocessing and model fitting see only training rows. The threshold
slider changes validation decisions. A reporting threshold is selected only
from validation evidence and then applied once to the reserved test partition.
Synthetic metrics demonstrate the workflow rather than expected real-world
performance.

## Browser build

The notebook carries exact PEP 723 browser dependencies. Marimo packages the
local `content_performance_classifier` source as a wheel during export. If an
exact scientific-package build is unavailable in Pyodide, Marimo records a
compatible browser build in the generated artifact; compare metrics within one
runtime artifact rather than assuming bitwise local/WASM parity.

```bash
uv run marimo export html-wasm src/app.py \
  -o build/content-performance-classifier \
  --mode run --execute --force
```

## Validation

From repository root:

```bash
uv run --project projects/content-performance-classifier pytest -q \
  projects/content-performance-classifier/tests
uv run --project projects/content-performance-classifier ruff check \
  projects/content-performance-classifier
uv run --project projects/content-performance-classifier ruff format --check \
  projects/content-performance-classifier
uv run --project projects/content-performance-classifier marimo check --strict \
  projects/content-performance-classifier/src/app.py
```

Current evidence: 27 focused tests, strict Marimo validation, executed WASM
package validation, and a Chromium interaction that changes the validation
threshold while the reserved-test reporting threshold remains fixed.

The committed Marimo session contains only the bundled synthetic fixture.
Release validation compares stable source hashes against a fresh session rather
than comparing volatile UI identifiers.

## Interpretation boundary

Synthetic labels come from an independent documented mechanism with bounded
noise. Resulting performance demonstrates workflow and evidence design. It does
not estimate production uplift, causal impact, or external validity.

See [PROVENANCE.md](PROVENANCE.md) for clean-room and data provenance.
