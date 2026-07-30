# Synthetic Wellness Data Pipeline

Production-oriented data engineering demonstration using only deterministic
synthetic data. Three source grains become one curated participant-day table,
a rejected-record ledger, and content-addressed audit evidence.

## What it demonstrates

- explicit input schemas and output grain
- stable validation and rejection semantics
- duration and dose unit normalization
- duplicate and unknown-reference handling
- pre-aggregation that prevents join multiplication
- deterministic fixtures, ordering, serialization, and SHA-256 hashes
- input immutability and idempotent reruns
- thin Marimo UI with bounded in-memory CSV uploads and explicit downloads

## Project layout

```text
app.py                           Marimo explorer
wellness_data_pipeline/          Tested domain package
tests/                           Behavior and notebook-import tests
PROVENANCE.md                    Data and clean-room provenance
pyproject.toml                   Runtime and development metadata
```

## Data contract

Inputs:

| Source | Grain |
|---|---|
| `participants` | one row per `participant_id` |
| `daily_signals` | one row per `participant_id` and `observed_on` |
| `interventions` | one row per intervention event |

Output:

`participant_days` contains one row per `participant_id` and `observed_on`.
Multiple interventions are aggregated before joining to that grain.

Rejected records expose only source, stable source-row identity, reason code,
and controlled safe detail. Raw uploaded rows are never copied into the ledger.

## Run locally

From this directory:

```bash
uv sync
uv run pytest -q
uv run marimo edit app.py
```

The default view uses generator version `wellness-synthetic-v1` and seed `2026`.
Users may instead provide all three CSV inputs. Each upload is capped at 2 MB
and 10,000 data rows, processed in the active notebook runtime, and never
written or sent over a network by this app. Explicit CSV downloads neutralize
spreadsheet formula prefixes in string cells.

## Validation

From repository root:

```bash
uv run --project projects/wellness-data-pipeline pytest -q \
  projects/wellness-data-pipeline/tests
uv run --project projects/wellness-data-pipeline ruff check \
  projects/wellness-data-pipeline
uv run --project projects/wellness-data-pipeline ruff format --check \
  projects/wellness-data-pipeline
uv run --project projects/wellness-data-pipeline marimo check --strict \
  projects/wellness-data-pipeline/app.py
```

## Scope

This project is an engineering demonstration, not a medical product. It makes no
clinical claims and provides no health advice. See [PROVENANCE.md](PROVENANCE.md)
for source and reuse boundaries.
