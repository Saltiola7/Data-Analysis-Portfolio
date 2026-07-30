---
title: Public-sector Opportunity Pipeline Backlog
status: active
last_updated: 2026-07-29
---

# Backlog

| id | title | priority | status | depends_on | owns | validation |
|---|---|---|---|---|---|---|
| PSOP-001 | Define domain, behavior, interfaces, and contracts | P0 | completed | - | project spec | Spec evidence |
| PSOP-002 | Write red normalization, incremental, retry, and parity tests | P0 | completed | PSOP-001 | tests | Expected failure evidence |
| PSOP-003 | Implement portable deterministic pipeline | P0 | completed | PSOP-002 | package | 66 focused tests and Ruff |
| PSOP-004 | Add Prefect adapter and parity evidence | P1 | completed | PSOP-003 | flow adapter | Portable core parity and flow construction |
| PSOP-005 | Build thin Marimo evidence explorer | P1 | completed | PSOP-003 | `app.py` | Strict check, WASM, session, and browser interaction |
| PSOP-006 | Add provenance and case-study evidence | P1 | completed | PSOP-005 | documentation | Claim and privacy review |

## Completed

| id | completed | evidence |
|---|---|---|
| PSOP-001 | 2026-07-29 | Approved specification |
| PSOP-002 | 2026-07-29 | Red normalization, boundary, retry, incremental, scoring, and parity evidence |
| PSOP-003 | 2026-07-29 | 66 focused tests and curated Ruff gates |
| PSOP-004 | 2026-07-29 | Portable core parity and Prefect flow-construction evidence |
| PSOP-005 | 2026-07-29 | Strict Marimo, executed WASM, synthetic session, and Chromium interaction |
| PSOP-006 | 2026-07-29 | Current case study, provenance, evidence, and limitations |
