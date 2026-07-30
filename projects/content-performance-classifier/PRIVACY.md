# Privacy

## Data boundary

The default demonstration uses deterministic fictional rows. Optional visitor
CSV files are parsed in memory and limited to 5 MB and 5,000 rows.

- Local Marimo: processing occurs in the local Python runtime.
- Molab or another server-hosted notebook: processing may occur in that hosted
  runtime. Do not treat it as browser-only.
- Exported Marimo WASM: processing occurs in the visitor's browser. The runtime
  may fetch application dependencies, but classifier code does not transmit
  uploaded content.

The project has no owner-operated upload backend, telemetry, database, object
storage, or persistence path. Reloading the runtime discards in-memory data.

## Downloads

Downloads happen only after explicit visitor action.

- `content_validation_predictions.csv` includes content identifiers and
  row-level validation predictions for the visitor's own review.
- `content_classifier_audit.json` contains aggregate lineage and evaluation
  evidence only. Uploaded category text is replaced with non-reversible
  per-dimension ordinal pseudonyms. It contains no rows or content identifiers.

## Publication rule

Only the bundled synthetic default may be captured in committed Marimo session
snapshots, screenshots, or hosted previews. Visitor uploads and their derived
outputs must never be committed, logged, or used as demo fixtures.
