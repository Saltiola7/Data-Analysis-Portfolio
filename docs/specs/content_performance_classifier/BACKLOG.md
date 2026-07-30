---
title: Content Performance Classifier Backlog
status: active
last_updated: 2026-07-29
---

# Backlog

| id | title | priority | status | depends_on | owns | validation |
|---|---|---|---|---|---|---|
| CPC-001 | Define domain, behavior, interfaces, and contracts | P0 | completed | - | project spec | Spec evidence |
| CPC-002 | Write red fixture, leakage, model, and evaluation tests | P0 | ready | CPC-001 | tests | Expected failure evidence |
| CPC-003 | Implement deterministic classifier package | P0 | pending | CPC-002 | package | Focused tests and Ruff |
| CPC-004 | Build thin threshold and error-analysis Marimo explorer | P1 | pending | CPC-003 | `app.py` | Strict check and export |
| CPC-005 | Add provenance and case-study evidence | P1 | pending | CPC-004 | documentation | Claim and privacy review |

## Completed

| id | completed | evidence |
|---|---|---|
| CPC-001 | 2026-07-29 | Approved specification |
