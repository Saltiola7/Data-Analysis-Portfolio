# Cloud, Data, and AI Platform Portfolio

Clean-room engineering portfolio by [Tommi Saltiola](https://www.linkedin.com/in/tommisaltiola/).

[Canonical GitHub repository](https://github.com/Saltiola7/data-portfolio)

Primary fit:

1. SEO/AEO Platform Engineer
2. Agentic AI Engineer
3. AI Platform Engineer
4. Forward Deployed Engineer for AI platforms
5. Cloud/Data Platform Engineer

The work emphasizes hands-on implementation: search intelligence, autonomous
workflows, cloud and data foundations, orchestration, observability, and
evidence-gated delivery.

## Flagship projects

| Project | Run | Engineering evidence | Tests |
|---|---|---|---:|
| [Synthetic Wellness Data Pipeline](projects/wellness-data-pipeline/README.md) | [Molab](https://molab.marimo.io/github/Saltiola7/data-portfolio/blob/main/projects/wellness-data-pipeline/app.py/wasm) | Three source grains, schema and grain contracts, dead letters, deterministic hashes, bounded uploads | 34 |
| [Content Performance Classifier](projects/content-performance-classifier/README.md) | [Molab](https://molab.marimo.io/github/Saltiola7/data-portfolio/blob/main/projects/content-performance-classifier/src/app.py/wasm) | Leakage-safe train/validation/reserved-test design, calibration, slice evidence, threshold governance, privacy-bounded exports | 27 |
| [Public-sector Opportunity Pipeline](projects/public-sector-opportunity-pipeline/README.md) | [Molab](https://molab.marimo.io/github/Saltiola7/data-portfolio/blob/main/projects/public-sector-opportunity-pipeline/app.py/wasm) | Heterogeneous ingestion, deterministic incremental merge, watermarks, retries, Prefect boundary, transparent scoring | 66 |

All three projects use only deterministic fictional data and pass focused tests,
Ruff, strict Marimo checks, executed WASM export validation, and real-browser
interaction smoke tests.

The wellness and classifier projects independently generalize concepts from
earlier DataCamp certification work. They use newly written code, schemas,
tests, metrics, and synthetic fixtures; assessment prompts, supplied datasets,
solutions, outputs, and certificate images are not published. The opportunity
pipeline similarly generalizes earlier multi-source Prefect work without
reusing its code, records, schemas, or endpoint contracts.

## Clean-room products

Two independent repositories turn deeper search and knowledge-system patterns
into public demonstrations without employer-code reuse:

- [Search Taxonomy Lab](https://github.com/Saltiola7/search-taxonomy-lab) —
  TF-IDF and latent-semantic evidence, cluster discovery, transparent
  classification, human review, benchmarks, and a hash-chained audit ledger.
- [Content Evidence Workbench](https://github.com/Saltiola7/content-evidence-workbench) —
  retrieval, exact citations, declared-entity context, judged evaluation, and
  explicit human review over a synthetic corpus.

GitHub source and this README are the portfolio front door. Molab runs reviewed
Marimo source on demand; there is no separately maintained portfolio site.

## Fixed-scope service

The [DBSCTR Delivery Accelerator](services/dbsctr-delivery-accelerator.md)
adapts an auditable agentic engineering lifecycle to one repository and
delivers one bounded pilot through every applicable gate.

[Discuss a pilot](mailto:tommi@tommisaltiola.com?subject=DBSCTR%20pilot) or
inspect the owner-authored, MIT-licensed
[DBSCTR source](https://github.com/Saltiola7/dotfiles-ai).

## Reproduce the evidence

Each project has its own `pyproject.toml` and `uv.lock`. From a project
directory:

```bash
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run marimo check --strict app.py
```

The classifier notebook lives at `src/app.py`. The
[quality workflow](.github/workflows/quality.yml) runs every project gate,
checks stable committed-session source identities, builds all three apps in a
temporary WASM test surface, exercises them in Chromium, scans critical
vulnerabilities, and emits an SPDX software bill of materials.

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

Owner-authored code is available under the [MIT License](LICENSE). Any future
public datasets retain their separately recorded source licenses.
