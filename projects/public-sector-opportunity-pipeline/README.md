# Public-sector Opportunity Pipeline

A clean-room portfolio project that demonstrates the platform work behind a
forward-deployed data product: heterogeneous ingestion, fail-closed validation,
dead letters, deterministic version selection, idempotent incremental merge,
watermarks, bounded retries, transparent ranking, orchestration boundaries, and
auditable exports.

All opportunities, organizations, identifiers, dates, and values are fictional.
The project never contacts a procurement endpoint.

## What it proves

- Two intentionally different synthetic source contracts normalize to one
  canonical row grain: one row per `source` and `source_id`.
- Invalid rows enter a controlled dead-letter ledger. Raw source payloads are
  not copied into rejection details.
- Versions are ordered by source update timestamp and then a SHA-256 content
  hash, including across separate incremental runs. The winner does not depend
  on input order.
- UTC timestamps retain fractional precision and are compared as timestamps,
  not lexicographically.
- Total record count is checked before source rows are copied. Source fields,
  text, sequences, numeric magnitudes, and value types have explicit bounds.
- Existing canonical rows must satisfy the full schema semantics even when
  their content hash has been recomputed.
- Existing newer versions cannot be overwritten by stale increments.
- Per-source watermarks advance only from accepted records.
- Re-running the same batch with returned canonical data and state is
  idempotent.
- Transient retries are bounded and observable. Permanent failures are never
  retried, and configured delays must be finite.
- `run_pipeline_from_adapters()` carries real adapter retry counts into the run
  manifest before invoking the same core.
- Prefect wraps, but does not replace, the portable core.
- The Marimo app imports no Prefect runtime and can run as a lightweight
  interactive evidence explorer.

## Architecture

```text
synthetic source A ─┐
                    ├─ validate/normalize ─ dead letters
synthetic source B ─┘          │
                               └─ version/dedupe ─ incremental merge
                                                       │
                                  state + hashes + transparent scoring
                                                       │
                                           Marimo evidence explorer

optional local Prefect flow ─────────────── invokes same portable core
```

## Transparent scoring

Scores are additive screening rules, never suitability probabilities:

- `+2` per preferred skill match, capped at `+4`
- `+2` for a preferred engagement type
- `+1` for `remote` or `flexible` when remote work is preferred
- `+1` when the opportunity ceiling meets the selected minimum

Every contribution, matched-skill list, explanation, and total appears in the
scored table. Preference types and values fail closed instead of being silently
dropped or coerced.

## Run locally

```bash
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run marimo check --strict app.py
uv run marimo edit app.py
```

Exercise the optional orchestration adapter:

```bash
uv run python -c "from public_sector_opportunity_pipeline.prefect_adapter import build_prefect_flow; print(build_prefect_flow().name)"
```

`run_prefect_pipeline(fixture)` provides offline core-parity execution.
`run_prefect_pipeline(fixture, use_engine=True)` runs the registered flow and
requires a configured Prefect API or an explicitly enabled isolated ephemeral
server.

Create the executed browser-only application:

```bash
uv run marimo export html-wasm app.py \
  -o build/public-sector-opportunity-pipeline \
  --mode run --no-show-code --execute --force
```

GitHub is the canonical source. A Molab deployment can clone this directory and
run `app.py`; Pages and Molab are derived views. The committed Marimo session
contains only the bundled fictional fixture. Release validation compares stable
source hashes against a fresh session rather than volatile UI identifiers.

## Project map

- `public_sector_opportunity_pipeline/`: portable domain and pipeline package
- `public_sector_opportunity_pipeline/prefect_adapter.py`: optional local flow
- `app.py`: thin Marimo view
- `tests/`: behavior, retry, parity, scoring, and export evidence
- `PROVENANCE.md`: clean-room and data lineage declaration
- `EVIDENCE.md`: retained red/green validation commands

Current evidence: 66 focused tests, strict Marimo validation, executed WASM
package validation, and a Chromium interaction that changes a fit preference
and observes recomputed rule contributions.

## Deliberate limits

- No live endpoint, authentication, contacts, notification, or application
  workflow
- No probabilistic ranking, LLM, vector search, or hidden scoring weight
- No multi-user persistence or uploaded-data retention
- No production scheduler, cloud resource, or service-level claim
- No claim that the optional Prefect engine path was executed by the retained
  local evidence; portable adapter parity and flow construction are tested
- No claim that fictional source fields mirror a real procurement contract

Those boundaries keep the MVP safe, reproducible, and easy to inspect.
