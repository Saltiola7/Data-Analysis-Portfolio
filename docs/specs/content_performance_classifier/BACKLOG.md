---
title: Content Performance Classifier Backlog
status: active
last_updated: 2026-07-29
---

# Backlog

| id | title | priority | status | depends_on | owns | validation |
|---|---|---|---|---|---|---|
| CPC-001 | Define domain, behavior, interfaces, and contracts | P0 | completed | - | project spec | Spec evidence |
| CPC-002 | Write red fixture, leakage, model, and evaluation tests | P0 | completed | CPC-001 | tests | Expected failure evidence |
| CPC-003 | Implement deterministic classifier package | P0 | completed | CPC-002 | package | 27 focused tests and Ruff |
| CPC-004 | Build thin threshold and error-analysis Marimo explorer | P1 | completed | CPC-003 | `src/app.py` | Strict check, WASM, session, and browser interaction |
| CPC-005 | Add provenance and case-study evidence | P1 | completed | CPC-004 | documentation | Claim and privacy review |
| CPC-006 | Add certification case-study imputation, benchmark, recall policy, and uncertainty | P0 | in_progress | CPC-005 | classifier package, app, tests, documentation | Public specification only | Grouped imputation, three-model validation benchmark, frozen recall policy, bootstrap interval, strict Marimo, WASM, and browser journey pass |

## Completed

| id | completed | evidence |
|---|---|---|
| CPC-001 | 2026-07-29 | Approved specification |
| CPC-002 | 2026-07-29 | Red fixture, split, leakage, evaluation, export, and privacy evidence |
| CPC-003 | 2026-07-29 | 27 focused tests and curated Ruff gates |
| CPC-004 | 2026-07-29 | Strict Marimo, executed WASM, synthetic session, and Chromium interaction |
| CPC-005 | 2026-07-29 | Current case study, provenance, privacy, and limitations |
