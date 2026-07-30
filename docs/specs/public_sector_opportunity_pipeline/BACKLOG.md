---
title: Public-sector Opportunity Pipeline Backlog
status: active
last_updated: 2026-07-29
---

# Backlog

| id | title | priority | status | depends_on | owns | validation |
|---|---|---|---|---|---|---|
| PSOP-001 | Define domain, behavior, interfaces, and contracts | P0 | completed | - | project spec | Spec evidence |
| PSOP-002 | Write red normalization, incremental, retry, and parity tests | P0 | ready | PSOP-001 | tests | Expected failure evidence |
| PSOP-003 | Implement portable deterministic pipeline | P0 | pending | PSOP-002 | package | Focused tests and Ruff |
| PSOP-004 | Add Prefect adapter and parity evidence | P1 | pending | PSOP-003 | flow adapter | Core/flow parity test |
| PSOP-005 | Build thin Marimo evidence explorer | P1 | pending | PSOP-003 | `app.py` | Strict check and export |
| PSOP-006 | Add provenance and case-study evidence | P1 | pending | PSOP-005 | documentation | Claim and privacy review |

## Completed

| id | completed | evidence |
|---|---|---|
| PSOP-001 | 2026-07-29 | Approved specification |
