---
title: Content Performance Classifier Changelog
---

# Changelog

## 2026-07-29 - Specification

- Defined a synthetic, leakage-aware content classification demonstration.
- Required baseline, calibration, threshold, slice, and error evidence.
- Prohibited employer-derived design and restricted assessment material.

## 2026-07-29 - Local MVP

- Implemented deterministic synthetic fixtures, immutable feature allowlisting,
  training-only preprocessing, and a 60/20/20 stratified split.
- Restricted threshold exploration to validation evidence and kept
  reserved-test reporting fixed.
- Passed 27 focused tests, Ruff, strict Marimo, executed WASM, synthetic-session
  source identity, privacy, and Chromium interaction gates.
