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

## 2026-07-30 - Certification case study expansion

- Added topic-family median imputation with training-global fallback.
- Added a validation-only benchmark across logistic regression, fixed random
  forest, and prevalence baseline.
- Added explicit minimum-recall threshold selection that maximizes validation
  precision and freezes the chosen policy before reserved-test evaluation.
- Added deterministic class-stratified reserved-test precision intervals.
- Added bounded synthetic missingness and app surfaces for benchmark, policy,
  and uncertainty evidence.
- Added direct Molab, source, and specification navigation from credential and
  project pages.
- Passed 36 focused tests, Ruff lint/format, strict Marimo, deterministic
  session comparison, executed WASM validation, and Chromium interaction.
- Implementation commit: `4fc687e`.
