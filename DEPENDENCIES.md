# Dependency and License Inventory

Each project-local `uv.lock` is the executable dependency authority. The root
`uv.lock` governs release-validation tools. GitHub Actions also emits a full
SPDX JSON software bill of materials for each validated release build.

## Direct runtime dependencies

| package | locked version | used by | declared license |
|---|---:|---|---|
| marimo | 0.23.15 | all three flagships | Apache-2.0 |
| pandas | 3.0.5 | all three flagships | BSD-3-Clause |
| NumPy | 2.5.1 | content classifier | BSD-3-Clause and bundled component licenses |
| scikit-learn | 1.9.0 | content classifier | BSD-3-Clause |
| Prefect | 3.8.0 | optional opportunity orchestration adapter | Apache-2.0 |

## Direct development and release dependencies

| package | locked version | purpose | declared license |
|---|---:|---|---|
| Playwright | 1.61.0 | browser interaction gates | Apache-2.0 |
| pytest | 9.1.1 | behavior and contract tests | MIT |
| Ruff | 0.16.0 | root, wellness, and classifier validation | MIT |
| Ruff | 0.14.14 | opportunity-pipeline validation | MIT |

The tables summarize direct dependencies; they do not replace transitive lock
metadata, generated SBOMs, or package license texts. Update this inventory
together with the affected lockfile.
