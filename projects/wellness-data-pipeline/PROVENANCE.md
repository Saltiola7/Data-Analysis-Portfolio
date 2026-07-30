# Provenance

## Origin

This project was created from a clean public specification on July 29, 2026.
Implementation, tests, schema, narrative, and fixtures were written for this
repository.

No employer source, client material, certification assessment material, private
repository history, personal data, screenshots, prompts, metrics, or
credentials were used.

## Data

All bundled records come from `generate_synthetic_fixture`.

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
