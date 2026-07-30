# Data Provenance

No external project dataset is admitted by default. Current portfolio apps use
deterministic fictional fixtures or bounded visitor uploads processed in the
visitor's browser.

Each project has a local provenance record. Together with its README and
declared code/schema contracts, the project evidence set records:

- immutable source identity or synthetic generator version
- owner and license
- collection date or on-demand generation timing plus admission-review date
- row grain and schema
- transformations
- privacy classification
- redistribution decision
- retention and replacement policy

## Current portfolio data

| Project family | Public data authority | Grain and lineage |
|---|---|---|
| Synthetic Wellness Data Pipeline | Project-owned deterministic generators | Source-specific fictional records are normalized under explicit schema and grain contracts; rejected records remain traceable through dead-letter evidence. |
| Content Performance Classifier | Project-owned deterministic generators | Fictional content-performance records are split under leakage and reserved-test contracts. |
| Public-sector Opportunity Pipeline | Project-owned deterministic generators | Fictional heterogeneous source records are normalized and merged under incremental-state and watermark contracts. |
| Analytics Learning Labs | `projects/analytics-learning-labs/analytics_learning_labs/fixtures.py` | Five deterministic synthetic fixtures declare generator version, seed, required columns, maximum rows, canonical observation grain, and an app-visible canonical CSV SHA-256. |

The learning labs do not contain historical notebook datasets. Their local
[provenance record](projects/analytics-learning-labs/PROVENANCE.md) maps each
historical theme to a newly written synthetic successor and records the
clean-room boundary.

## Restricted source boundary

Historical learning notebooks and certification assessment artifacts were used
only for private admission review and broad theme discovery. Their source code,
prose, supplied datasets, exact schemas, metrics, outputs, grader rules, and
history are not public data sources and are not required to reproduce any
portfolio result.

Professional certificate JPEG files are owner-provided screenshots of
issuer-issued credential evidence, not analytical datasets. Their public
purpose, checksums, dimensions, visible content, metadata review, and official
verification records live in
[CERTIFICATIONS.md](CERTIFICATIONS.md). They are not inputs to any analysis or
model.

## Runtime-only visitor data

User-uploaded demo data remains runtime-only and is never committed, logged,
snapshotted, or added to portfolio fixtures. The public Molab links use `/wasm`
so bounded uploads are processed in the visitor's browser rather than an
owner-operated backend.

No learning lab accepts an upload or sends fixture data to an owner backend.
Changing a seed recomputes fictional values in active browser memory only.
