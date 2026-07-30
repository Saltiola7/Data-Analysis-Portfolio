---
title: Public Engineering Portfolio
status: approved
type: product
version: 1.2
last_updated: 2026-07-30
bounded_context: public_portfolio
risk: elevated
delivery_intent: draft-pr
product_intent: docs/specs/public_portfolio/PRODUCT.md
---

# Public Engineering Portfolio

## Engineering Profile

| Field | Contract |
|---|---|
| Accountable owner | Tommi Saltiola |
| Canonical source | `Saltiola7/data-portfolio` |
| Working branch | DBSCTR cycle branch reviewed through a pull request |
| Runtime | Python 3.12-3.14 and Marimo 0.23.15 |
| Package authority | `pyproject.toml` and `uv.lock` |
| Public data | Synthetic or explicitly redistributable only |
| Browser delivery | GitHub-backed Molab `/wasm` links |
| Accessibility | WCAG 2.2 AA |
| Validation | pytest, Ruff, strict Marimo check, temporary WASM export, browser review, privacy and provenance audits |
| Security owner | Repository owner |
| Recovery owner | Repository owner through private recovery bundle and local refs |
| Integration boundary | Pull-request review; no direct public `main` mutation |

Applicable DBSCTR modules: Python, Security, Data, ML/AI, Analytics, Web, and
Cloud for deployment preparation.

## Architecture

```mermaid
graph TD
    accTitle: GitHub portfolio source, validation, and on-demand browser delivery
    accDescr: Owner-authored projects and synthetic fixtures enter canonical GitHub source. CI validates source and temporary WASM exports. Molab reads the same source on demand. Runtime visitor uploads remain outside owner storage.

    AUTHOR["Owner-authored projects"]
    FIXTURES["Synthetic fixtures"]
    SRC["Canonical GitHub repository"]
    README["GitHub README and project evidence"]
    CI["Tests, Marimo, privacy, provenance, temporary WASM"]
    MOLAB["GitHub-backed Molab /wasm"]
    VISITOR["Recruiter or client"]
    UPLOAD["Optional visitor upload"]
    MEMORY["Active browser/runtime memory"]
    DOWNLOAD["Explicit visitor download"]

    AUTHOR --> SRC
    FIXTURES --> SRC
    SRC --> README
    SRC --> CI
    SRC --> MOLAB
    README --> VISITOR
    MOLAB --> VISITOR
    VISITOR --> UPLOAD
    UPLOAD --> MEMORY
    MEMORY --> DOWNLOAD
```

## Visual Evidence

| Concern | Decision |
|---|---|
| Boundary | required: architecture and trust-boundary flow above |
| Interaction | not applicable: individual project specs own interactive behavior |
| State | not applicable: publication approval is a gate, not a runtime state machine |
| Data/trust | required: architecture and trust-boundary flow above |
| Schema | not applicable: project specs own persistent and tabular schemas |
| Dependency/deployment | required: architecture and trust-boundary flow above |
| Quantitative | not applicable: no portfolio decision depends on a measured comparison |

**Review question:** Can public source reach a visitor only through validated
derived views, while visitor uploads remain outside owner storage?

**Text equivalent:** Owner-authored projects and synthetic fixtures enter the
canonical GitHub repository. CI validates source plus temporary WASM exports.
Visitors inspect the GitHub README and evidence or open a source-pinned Molab
`/wasm` app. A visitor can optionally place a bounded upload in the active
browser runtime and explicitly download derived output; no owner backend
receives or retains it.

Canonical source: this specification. Owner: repository owner. Change trigger:
project admission, validation, delivery, upload, or retention boundaries change.

## Domain

| Term | Meaning |
|---|---|
| flagship | Current, tested project aligned with target contract roles |
| public fixture | Synthetic or redistributable data with recorded lineage |
| evidence packet | Tests, metrics, provenance, limitations, and source identity |
| browser demo | On-demand Molab `/wasm` view using public or runtime-only data |
| clean root | Branch with no parent relationship to old public history |
| legacy | Repaired historical work that passes current gates; empty initially |
| clean-room successor | Independent implementation that generalizes a prior idea without copying restricted artifacts |

Entities:

- `PortfolioProject`, identified by project slug
- `PublicFixture`, identified by path and SHA-256
- `MarimoApp`, identified by source path and commit
- `Deployment`, identified by source commit and public URL
- `ServiceOffer`, identified by product and scope version

## Behavior

### Admit a project

Given a project has owner-authored code, synthetic or cleared data, tests,
provenance, and limitations, when all project gates pass, then it appears as a
flagship with traceable source and evidence.

### Reject contaminated material

Given a candidate contains employer, client, restricted assessment prompt,
assessment data, assessment solution code, personal, credential-image, or
unknown-license material, when admission runs, then publication fails and no
public source or derived runtime includes it.

### Admit a clean-room successor

Given a prior project supplies only conceptual inspiration, when new behavior,
code, fixtures, schemas, tests, metrics, and documentation are independently
implemented and the ancestry is disclosed, then the successor may be admitted.

### Run without private dependencies

Given a visitor opens a demo without credentials or private infrastructure,
when the default path runs, then it produces a useful deterministic result from
public fixtures or runtime-only uploaded data.

### Preserve private uploads

Given a visitor uploads supported data, when browser-local processing runs, then
the data is not committed, logged, snapshotted, or retained by an owner backend.

### Retire the static portfolio site

Given GitHub source is canonical, when repository-only publication is enabled,
then the static `site/` tree, Pages deployment actions, Pages permissions, and
Pages URLs are absent while GitHub evidence and Molab links remain usable.

## Contracts

- Every tracked path is intentionally authored or admitted.
- No `node_modules`, private path, secret-like value, PII artifact, client
  identifier, or unknown-license dataset is reachable from clean-root history.
- Raw assessment prompts, datasets, solutions, outputs, and certificate images
  are excluded; official credential links may be used.
- Every fixture has schema, grain, generator or source, license, and SHA-256.
- Every notebook passes strict Marimo validation and fresh-clone execution.
- Every README or project claim maps to code, tests, or an owner-approved fact.
- The repository contains no `site/` tree and CI contains no Pages upload,
  deployment action, environment, or write permission.
- The root README links the canonical GitHub repository and each admitted
  flagship's GitHub-backed Molab `/wasm` runtime.
- User-uploaded data and BYOK credentials are runtime-only.
- Browser demos expose loading, empty, success, validation, and error states.
- Public integration identifies source SHA, rollback ref, compatibility, and
  CI health.

## Initial Flagships

1. Synthetic wellness data pipeline
2. Content performance classifier
3. Public-sector opportunity pipeline
4. Search Taxonomy Lab, linked from its independent repository
5. Content Evidence Workbench, linked from its independent repository
6. DBSCTR Delivery Accelerator, linked from its canonical MIT repository

The raw DataCamp certification solutions and the legacy Netflix, judo, cancer,
airline, and restaurant-location notebooks are not admitted. The first two
flagships above are independently implemented synthetic successors to the
strongest certification concepts. A restaurant-location data-quality app may
enter a later cycle only after independent data and license provenance exist.

## Validation

```bash
uv run --frozen pytest -q
uv run --frozen ruff check scripts tests
uv run --frozen ruff format --check scripts tests
uv run --frozen python scripts/validate_wasm_export.py <export> --package <package>
uv run --frozen python scripts/browser_smoke.py <site> --scenario <journey>
```

Project-local locked environments run focused pytest, Ruff, strict Marimo,
session-source, and temporary executed-WASM gates. Integration also adds
clean-history, privacy, browser interaction, vulnerability, SBOM, and
source-identity checks.

## Gate Ledger

| Gate | Applicability | Required result |
|---|---|---|
| Domain | required | Terms, owners, trust boundaries, and modules fixed |
| Behavior | required | Admission, rejection, runtime, privacy, and retirement scenarios fixed |
| Spec | required | Project layout, interfaces, dependencies, and backlog fixed |
| Contract | required | Privacy, provenance, reproducibility, and release invariants executable |
| Test-driven implementation | required | Red then green project evidence |
| Refactor | required | Coherent source and current documentation |
| Review/Integrate | required | Traceability, compatibility, and affected scope reviewed |
| Release | not applicable | Draft pull request creates no versioned release |
| Deploy | required | Pages stays disabled and public route returns not found |
| Operate | not applicable | No running owner service |
| Maintain/Retire | required | Support, dependency, data, and retirement obligations documented |
