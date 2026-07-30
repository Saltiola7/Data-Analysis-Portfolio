# Provenance and clean-room boundary

## Authorship

This project was designed and implemented as new portfolio code from an approved
behavior and contract specification. It does not copy employer, client,
DataCamp assessment, SaaS Pegasus, premium template, or third-party repository
source.

## Data lineage

`generate_synthetic_sources()` creates every source row in memory from:

- a caller-visible integer seed;
- hand-authored fictional organizations and opportunity descriptions;
- deterministic Python standard-library generation.

No live procurement API, web page, contact record, private file, credential,
personal data, or user upload is read. Deliberately invalid fixture rows exist
only to demonstrate validation and dead-letter behavior.

## Transform lineage

1. Federal-shaped and municipal-shaped fictional mappings enter memory.
2. Source adapters enforce record, field, text, sequence, number, and type
   bounds before copying only fields from the declared source contracts.
3. Invalid rows become controlled reason codes without raw-payload copying.
4. Valid rows receive canonical identities, schema version `1.0`, and SHA-256
   content identities.
5. Duplicate and existing versions merge deterministically by parsed UTC
   timestamp and content identity, including same-timestamp versions received
   in separate runs.
6. Accepted update timestamps advance per-source watermarks.
7. Canonical rows, rejected rows, and state receive stable SHA-256 hashes.
8. Optional additive scoring creates derived contribution columns.
9. Explicit CSV exports neutralize spreadsheet formula prefixes.

## Dependencies

- Python: runtime and standard-library contracts
- pandas: deterministic tabular representation and export
- Marimo: interactive evidence explorer
- Prefect: optional orchestration adapter only
- pytest and Ruff: development validation

Exact resolved artifacts are recorded in `uv.lock`.

## Distribution

Source is intended for an MIT-licensed public portfolio. GitHub remains
canonical. Molab or generated HTML previews are derived runtimes and must not
introduce private data or credentials.
