# Provenance

## Origin

This project was independently implemented from a clean public specification
on July 29, 2026. It generalizes data-contract, unit-normalization, joining, and
validation concepts from the owner's earlier data-engineering certification
work.

No assessment prompt, supplied dataset, solution code, exact schema, threshold,
metric, output, credential image, employer source, client material, private
repository history, personal data, or screenshot was copied. Implementation,
tests, schemas, narrative, and synthetic fixtures were written for this
repository.

## Data

All bundled records come from `generate_synthetic_fixture`.

- owner: Tommi Saltiola
- source license: repository MIT license
- generation timing: on demand; no generated dataset is committed
- admission review date: `2026-07-29`
- generator version: `wellness-synthetic-v1`
- default seed: `2026`
- generator: Python standard-library pseudorandom number generator
- network access: none
- external datasets: none
- personal data: none

The generated identifiers, cohorts, measurements, interventions, and controlled
invalid rows are fictional. They exist only to exercise public pipeline
contracts.

## User uploads

Marimo uploads are optional and bounded to 2 MB per CSV. The app reads bytes in
the active runtime, does not persist them, performs no network calls, and places
only controlled error details in its rejected ledger. Downloads occur only
after explicit user action.

## Reproducibility

Identical inputs and schema version produce identical curated rows, rejected
rows, ordering, and SHA-256 hashes. Changing the fixture seed changes generated
measurements while preserving schemas and validation behavior.

## Privacy, redistribution, and retention

Bundled fixture privacy classification is public synthetic data. Optional
uploads are visitor-controlled runtime data and are not redistributed,
committed, logged, or retained by an owner backend. Independently written
source and documentation are redistributed under the repository MIT license;
generated rows are transient evidence, not a published dataset.

The retained authority is generator and pipeline source, schema contracts,
tests, hashes, and this record. If lineage or privacy cannot be reproduced, the
public demo link is removed until replacement evidence passes review.
