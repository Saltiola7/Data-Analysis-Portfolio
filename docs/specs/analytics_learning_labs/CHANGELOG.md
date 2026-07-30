# Analytics Learning Labs Changelog

## 2026-07-30 - Direct Molab runtime repair

- Replaced shell-only direct Molab routes with an import-closed PEP 723
  dependency on a deterministic pure-Python wheel pinned to immutable commit
  `408740d` and SHA-256.
- Added fail-closed validation of the lock, immutable wheel blob, package-source
  parity, exact dependency metadata, RECORD hashes and sizes, duplicate archive
  members, private paths, and all five app headers.
- Added exact-commit Molab browser journeys that enter the embedded application
  frame, inspect structured worker events, reject runtime exceptions, and
  require success, fixture, and table outputs from one non-null kernel run
  before testing seed recomputation.
- Revalidated all eight local WASM applications and all five immutable Molab
  routes. The repository now has 311 focused root and project tests.
- Implementation through commit `cffe59b`.

## 2026-07-30 - Initial clean-room delivery

- Delivered five deterministic synthetic Marimo labs at explicit analytical
  grain with shared schema, validation, analysis, presentation, and provenance
  contracts.
- Added completed-flight airline denominators, agreeing-profile cohort
  deduplication, non-circular fictional health bands, a restaurant unresolved
  ledger, unique streaming chart labels, and stable athlete dimensions.
- Added canonical fixture SHA-256 evidence, five pinned default hashes, exact
  pandas 3.0.2 host/browser identity, and fail-closed valid and empty seed
  behavior.
- Added 125 focused tests, Ruff, strict Marimo checks, five executed WASM
  exports, local-wheel privacy/error scanning, five Chromium journeys, and live
  kernel recomputation evidence.
- Published two owner-approved screenshots of issuer-issued credentials with
  exact checksums while excluding all assessment and raw notebook material.
- Recorded the Marimo 0.23.15 raw-markup `aria-label` limitation; WCAG 2.2 AA
  remains a target.
- Implementation commit: `19a8757`.
