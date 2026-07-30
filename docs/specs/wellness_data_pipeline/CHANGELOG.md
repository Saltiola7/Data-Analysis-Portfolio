---
title: Synthetic Wellness Data Pipeline Changelog
---

# Changelog

## 2026-07-29 - Specification

- Defined synthetic source grains and participant-day output.
- Added unit normalization, rejected-record, idempotency, and join-cardinality
  contracts.
- Prohibited certification assessment material and private data.

## 2026-07-29 - Local MVP

- Added deterministic synthetic fixtures, validation, normalization,
  participant-day aggregation, rejected-record evidence, and canonical hashes.
- Added a Marimo explorer with bounded in-memory CSV uploads and explicit
  downloads.
- Added fail-closed UTF-8 parsing, a 10,000-row input limit, and
  spreadsheet-formula-safe CSV serialization after security review.
- Locked the Python environment and passed 34 focused tests, curated Ruff
  checks, strict Marimo validation, executed WASM package validation, and a
  Chromium seed-recomputation journey.
- Added a synthetic-only committed session with stable source-hash validation;
  volatile Marimo UI identifiers are not treated as source drift.
