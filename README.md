# Data Portfolio

Clean-room data engineering and applied analytics portfolio by
[Tommi Saltiola](https://www.linkedin.com/in/tommisaltiola/).

[Canonical GitHub repository](https://github.com/Saltiola7/data-portfolio)

The portfolio emphasizes reproducible analysis, explicit data contracts,
deterministic synthetic fixtures, browser-runnable evidence, and test-driven
delivery. GitHub source is the portfolio front door; Molab derives each
interactive Marimo app from that reviewed source on demand.

## Flagship projects

| Project | Run | Engineering evidence | Tests |
|---|---|---|---:|
| [Synthetic Wellness Data Pipeline](projects/wellness-data-pipeline/README.md) | [Molab](https://molab.marimo.io/github/Saltiola7/data-portfolio/blob/main/projects/wellness-data-pipeline/app.py/wasm) | Three source grains, schema and grain contracts, dead letters, deterministic hashes, bounded uploads | 34 |
| [Content Performance Classifier](projects/content-performance-classifier/README.md) | [Molab](https://molab.marimo.io/github/Saltiola7/data-portfolio/blob/main/projects/content-performance-classifier/src/app.py/wasm) | Leakage-safe train/validation/reserved-test design, calibration, slice evidence, threshold governance, privacy-bounded exports | 27 |
| [Public-sector Opportunity Pipeline](projects/public-sector-opportunity-pipeline/README.md) | [Molab](https://molab.marimo.io/github/Saltiola7/data-portfolio/blob/main/projects/public-sector-opportunity-pipeline/app.py/wasm) | Heterogeneous ingestion, deterministic incremental merge, watermarks, retries, Prefect boundary, transparent scoring | 66 |

All three flagships use deterministic fictional data and pass focused tests,
Ruff, strict Marimo checks, executed WASM export validation, and Chromium
interaction smoke tests.

The wellness and classifier projects independently generalize broad competency
areas demonstrated through professional certification. They use newly written
code, schemas, tests, metrics, and synthetic fixtures. The opportunity pipeline
similarly generalizes earlier multi-source orchestration work without reusing
private code, records, schemas, or endpoint contracts.

## Supporting learning labs

These smaller labs modernize five historical learning themes as independently
written Marimo apps. They are supporting analytical demonstrations, not claims
of production deployment. Every default path uses deterministic synthetic data
and runs without credentials, uploads, or private infrastructure.

| Lab | Run | Analytical focus |
|---|---|---|
| [Airline Delay Quality Lab](projects/analytics-learning-labs/README.md#airline-delay-quality-lab) | [Molab](https://molab.marimo.io/github/Saltiola7/data-portfolio/blob/main/projects/analytics-learning-labs/apps/airline_delays.py/wasm) | Flight-grain delay components, cancellation context, and carrier summaries |
| [Synthetic Health Risk Quality Lab](projects/analytics-learning-labs/README.md#synthetic-health-risk-quality-lab) | [Molab](https://molab.marimo.io/github/Saltiola7/data-portfolio/blob/main/projects/analytics-learning-labs/apps/synthetic_cohort.py/wasm) | Duplicate-profile audit and descriptive ordinal associations over fictional data |
| [Restaurant Location Quality Lab](projects/analytics-learning-labs/README.md#restaurant-location-quality-lab) | [Molab](https://molab.marimo.io/github/Saltiola7/data-portfolio/blob/main/projects/analytics-learning-labs/apps/restaurant_locations.py/wasm) | Coordinate validation, accepted records, and an explicit unresolved ledger |
| [Streaming Catalog Explorer](projects/analytics-learning-labs/README.md#streaming-catalog-explorer) | [Molab](https://molab.marimo.io/github/Saltiola7/data-portfolio/blob/main/projects/analytics-learning-labs/apps/streaming_catalog.py/wasm) | Release-period, genre, and duration summaries at title grain |
| [Judo Medal Explorer](projects/analytics-learning-labs/README.md#judo-medal-explorer) | [Molab](https://molab.marimo.io/github/Saltiola7/data-portfolio/blob/main/projects/analytics-learning-labs/apps/sports_outcomes.py/wasm) | Medal-rate summaries at declared fictional athlete-event grain |

See the [Analytics Learning Labs evidence](projects/analytics-learning-labs/README.md)
and [clean-room provenance](projects/analytics-learning-labs/PROVENANCE.md).

## Professional certifications

Owner-approved DataCamp Data Scientist and Data Engineer certificates are
published as professional evidence with official verification links, exact
checksums, visible-content review, and metadata review.

[Review certifications and competency mapping](CERTIFICATIONS.md).

Certificate images do not admit any associated assessment prompts, datasets,
solutions, schemas, metrics, outputs, or grader rules into this repository.

## Independent clean-room products

Two separate repositories turn deeper search and knowledge-system patterns into
public demonstrations without employer-code reuse:

- [Search Taxonomy Lab](https://github.com/Saltiola7/search-taxonomy-lab) —
  TF-IDF and latent-semantic evidence, cluster discovery, transparent
  classification, human review, benchmarks, and a hash-chained audit ledger.
- [Content Evidence Workbench](https://github.com/Saltiola7/content-evidence-workbench) —
  retrieval, exact citations, declared-entity context, judged evaluation, and
  explicit human review over a synthetic corpus.

## Fixed-scope service

The [DBSCTR Delivery Accelerator](services/dbsctr-delivery-accelerator.md)
adapts an auditable agentic engineering lifecycle to one repository and
delivers one bounded pilot through every applicable gate.

[Discuss a pilot](mailto:tommi@tommisaltiola.com?subject=DBSCTR%20pilot) or
inspect the owner-authored, MIT-licensed
[DBSCTR source](https://github.com/Saltiola7/dotfiles-ai).

## Reproduce the evidence

Each flagship has its own `pyproject.toml` and `uv.lock`. From the repository
root, run the matching app path inside each project:

```bash
(cd projects/wellness-data-pipeline && uv sync --locked && uv run --frozen pytest -q && uv run --frozen marimo check --strict app.py)
(cd projects/content-performance-classifier && uv sync --locked && uv run --frozen pytest -q && uv run --frozen marimo check --strict src/app.py)
(cd projects/public-sector-opportunity-pipeline && uv sync --locked && uv run --frozen pytest -q && uv run --frozen marimo check --strict app.py)
```

Project-local README files list their complete Ruff and verification commands.
The five learning labs share one locked environment:

```bash
(
  cd projects/analytics-learning-labs
  uv sync --locked
  uv run --frozen pytest -q
  uv run --frozen ruff check .
  uv run --frozen ruff format --check .
  uv run --frozen marimo check --strict apps/*.py
)
```

The [quality workflow](.github/workflows/quality.yml) runs project gates, builds
all eight apps in temporary WASM test surfaces, exercises them in Chromium,
scans critical vulnerabilities, and emits an SPDX software bill of materials.

## Trust boundary

This repository starts from an empty public-history root. It contains no
employer code, client data, private credentials, restricted assessment prompts,
datasets, solutions or outputs, proprietary SaaS source, or personal datasets.
Visitor uploads remain runtime-only and are never admitted to committed session
previews.

See [CLEAN_ROOM.md](CLEAN_ROOM.md), [DATA_PROVENANCE.md](DATA_PROVENANCE.md),
and [DEPENDENCIES.md](DEPENDENCIES.md).

## Publication model

[`Saltiola7/data-portfolio`](https://github.com/Saltiola7/data-portfolio) is the
canonical public portfolio. Separate static hosting is retired. Molab derives
each runnable app directly from reviewed GitHub source. Changes integrate
through pull-request review.

## License

Owner-authored code and documentation are available under the
[MIT License](LICENSE). Professional credential images are published solely as
verification evidence and are not licensed for reuse under the repository's
MIT license. Any future public datasets retain their separately recorded source
licenses.
