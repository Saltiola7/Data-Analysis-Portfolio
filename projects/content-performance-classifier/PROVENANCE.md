# Provenance

## Origin

This project was independently implemented from a clean public specification
on July 29, 2026. It generalizes classification and evaluation concepts from
the owner's earlier data-science certification work and reframes them for
synthetic content-performance evidence.

No assessment prompt, supplied dataset, solution code, exact schema, feature
set, label, threshold, metric, output, credential image, employer source,
client material, private repository history, personal data, screenshot, or
taxonomy was copied. Implementation, tests, feature contract, narrative, and
fixture generator were written for this repository.

## Synthetic data

All bundled rows come from `generate_synthetic_content`.

- owner: Tommi Saltiola
- source license: repository MIT license
- generation timing: on demand; no generated dataset is committed
- admission review date: `2026-07-29`
- generator version: `content-performance-synthetic-v1`
- default seed: `2026`
- random generator: NumPy `default_rng`
- data subjects: fictional content items
- network access: none
- external datasets: none
- personal data: none

The generator samples independent feature distributions. A documented logistic
mechanism combines query coverage, internal links, entities, update cadence,
age, word count, readability, and small synthetic category effects. Labels are
sampled from probabilities mixed with bounded noise. This mechanism was written
for demonstration and does not reproduce an employer or assessment design.

## User uploads

Marimo uploads are optional, limited to strict UTF-8 CSV files no larger than
5 MB or 5,000 rows, and processed only in the active runtime. The app performs
no upload-content transmission or persistence. A hosted notebook runtime may
process uploads remotely; the WASM build processes them in the visitor's
browser. Runtimes may still fetch application dependencies. CSV and audit
downloads occur only after explicit user action.

## Reproducibility and lineage

Training records fixture/source hashes, feature allowlist, seed, three-way split
identity, model parameters, validation-selected threshold, model hash, and
partition probability hashes. Identical input and seed produce identical
splits, probabilities, metrics, and exports under the locked environment.

The metadata-only audit contains aggregate validation and reserved-test
evidence. Arbitrary categorical values are replaced with per-dimension ordinal
pseudonyms such as `category-001`; no reversible category hash is emitted. Raw
rows and content identifiers are excluded. The explicit predictions CSV is a
different artifact and includes validation content identifiers so its owner can
review errors.

Marimo may resolve a different Pyodide-compatible scientific-package build for
the WASM export when the local exact build is unavailable in-browser. The
exact live browser patch is not currently asserted. Deterministic claims apply
to the locked host environment; the executed Chromium journey establishes
browser compatibility, not cross-version numerical identity.

## Privacy, redistribution, and retention

Bundled fixture privacy classification is public synthetic data. Optional
uploads are visitor-controlled runtime data; they are not admitted to source,
session snapshots, or owner storage. Independently written source and
documentation are redistributed under the repository MIT license. Generated
rows and models are transient evidence unless the visitor explicitly downloads
an artifact.

The retained authority is generator, feature and split contracts, model and
audit code, tests, hashes, locks, and this record. If lineage, privacy, or
reserved-test integrity cannot be reproduced, the public demo link is removed
until replacement evidence passes review.
