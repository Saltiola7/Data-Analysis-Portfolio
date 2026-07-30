# Dependency and License Inventory

Each project-local `uv.lock` is the executable dependency authority. The root
`uv.lock` governs repository-validation tools. GitHub Actions also emits a full
SPDX JSON software bill of materials for each validated CI build.

## Direct runtime dependencies

| Package | Locked version | Purpose and consumers | Declared license | Lock authority | Browser/WASM boundary |
|---|---:|---|---|---|---|
| marimo | 0.23.15 | Reactive notebook runtime for three flagships and five learning labs | Apache-2.0 | Each project-local `uv.lock` | Included in derived Molab and executed WASM runtimes |
| pandas | 3.0.5 | Host-side tabular contracts, fixtures, transformation, and analysis for the three flagships | BSD-3-Clause | Flagship project `uv.lock` files | Executed Chromium journeys prove current Pyodide compatibility; the exact browser pandas patch is not asserted for these three apps |
| pandas | 3.0.2 | Host and browser tabular contracts, fixtures, transformation, and analysis for the five learning labs | BSD-3-Clause | `projects/analytics-learning-labs/uv.lock` | Pinned in the lock and five PEP 723 requests; seed-change browser journeys assert the live runtime version after recomputation |
| NumPy | 2.5.1 | Numerical operations used by the content classifier | BSD-3-Clause and bundled component licenses | `projects/content-performance-classifier/uv.lock` | Included in the classifier's derived browser runtime |
| scikit-learn | 1.9.0 | Modeling, calibration, and evaluation used by the content classifier | BSD-3-Clause | `projects/content-performance-classifier/uv.lock` | Included in the classifier's derived browser runtime |
| Prefect | 3.8.0 | Optional orchestration adapter for the opportunity pipeline | Apache-2.0 | `projects/public-sector-opportunity-pipeline/uv.lock` | Not required by the default browser path; orchestration boundary remains separately testable |

## Owner-authored local packages

| Package | Used by | License | Browser/WASM boundary |
|---|---|---|---|
| `wellness_data_pipeline` | Synthetic Wellness Data Pipeline | MIT | Exactly one local wheel is embedded and validated in its executed WASM export |
| `content_performance_classifier` | Content Performance Classifier | MIT | Exactly one local wheel is embedded and validated in its executed WASM export |
| `public_sector_opportunity_pipeline` | Public-sector Opportunity Pipeline | MIT | Exactly one local wheel is embedded and validated in its executed WASM export |
| `analytics_learning_labs` | Five Analytics Learning Labs | MIT | Exactly one shared local wheel is embedded and validated in every learning-lab WASM export |

## Direct development and validation dependencies

| Package | Locked version | Purpose | Declared license | Lock authority | Runtime boundary |
|---|---:|---|---|---|---|
| Playwright | 1.61.0 | Chromium interaction and console/page-error gates | Apache-2.0 | Root `uv.lock` | CI and local validation only; not shipped to visitors |
| pytest | 9.1.1 | Behavior, contract, provenance, and repository acceptance tests | MIT | Root and project-local `uv.lock` files | Validation only; not shipped as app behavior |
| Ruff | 0.16.0 | Root, wellness, classifier, and learning-lab lint/format gates | MIT | Root and relevant project-local `uv.lock` files | Validation only |
| Ruff | 0.14.14 | Opportunity-pipeline lint/format gate | MIT | `projects/public-sector-opportunity-pipeline/uv.lock` | Validation only |
| Hatchling | 1.31.0 | Local-wheel build backend for the five learning labs | MIT | `projects/analytics-learning-labs/pyproject.toml` and `uv.lock` | Build isolation only; not imported by the browser application |

## Update contract

The tables summarize direct dependencies; they do not replace transitive lock
metadata, generated SBOMs, package license texts, or vulnerability scans.
Update this inventory together with the affected lockfile whenever a direct
dependency, version, purpose, license, or browser boundary changes.
