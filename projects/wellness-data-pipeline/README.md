# Data Engineer Certification Case Study: Synthetic Wellness Data Pipeline

Production-oriented data engineering demonstration using only deterministic
synthetic data. Four source grains become one curated participant-day table,
a rejected-record ledger, and content-addressed audit evidence.

[Run in Molab](https://molab.marimo.io/github/Saltiola7/data-portfolio/blob/main/projects/wellness-data-pipeline/app.py/wasm)
· [Review source](wellness_data_pipeline/)
· [Review engineering specification](../../docs/specs/wellness_data_pipeline/README.md)

## What it demonstrates

- explicit input schemas and output grain
- stable validation and rejection semantics
- duration and dose unit normalization
- duplicate and unknown-reference handling
- aggregate source profiles without raw-value disclosure
- pre-aggregation that prevents join multiplication
- deterministic fixtures, ordering, serialization, and SHA-256 hashes
- input immutability and idempotent reruns
- thin Marimo UI with bounded in-memory CSV uploads and explicit downloads

## Project layout

```text
app.py                           Marimo explorer
wellness_data_pipeline/          Tested domain package
tests/                           Behavior and notebook-import tests
__marimo__/session/app.py.json   Synthetic static preview
PROVENANCE.md                    Data provenance
pyproject.toml                   Runtime and development metadata
```

## Data contract

Inputs:

| Source | Grain |
|---|---|
| `participants` | one row per `participant_id` |
| `programs` | one row per `program_id` |
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
uv sync --locked
uv run pytest -q
uv run marimo edit app.py
```

The default view uses generator version `wellness-synthetic-v2` and seed `2026`.
Users may instead provide all four CSV inputs. Each upload is capped at 2 MB
and 10,000 data rows, processed in the active notebook runtime, and never
written or sent over a network by this app. Explicit CSV downloads neutralize
spreadsheet formula prefixes in string cells.

## Browser build

The notebook carries exact PEP 723 browser dependencies. Marimo packages the
local `wellness_data_pipeline` source as a wheel during export.

```bash
uv run marimo export html-wasm app.py \
  -o build/wellness-data-pipeline \
  --mode run --no-show-code --execute --force
```

The committed Marimo session contains only the bundled synthetic fixture.
Release validation regenerates a fresh session, compares stable script and cell
source hashes, and ignores volatile browser-control identifiers.

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

Current evidence: 36 focused tests, strict Marimo validation, executed WASM
package validation, and a Chromium interaction that changes the synthetic seed
and observes recomputed evidence.

## Scope

This project is an engineering demonstration, not a medical product. It makes no
clinical claims and provides no health advice. See [PROVENANCE.md](PROVENANCE.md)
for data provenance and reuse boundaries.
