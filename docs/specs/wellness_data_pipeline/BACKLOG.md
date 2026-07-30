---
title: Synthetic Wellness Data Pipeline Backlog
status: active
last_updated: 2026-07-29
---

# Backlog

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
|---|---|---|---|---|---|---|---|---|---|---|
| WELL-001 | Define domain, behavior, interfaces, and contracts | P0 | completed | - | project spec | portfolio product intent | no | TDD requires stable contracts | S | Spec evidence passes |
| WELL-002 | Write red pipeline and fixture tests | P0 | ready | WELL-001 | project tests | project spec | no | Behavior evidence precedes implementation | M | Tests fail for missing implementation |
| WELL-003 | Implement deterministic pipeline and synthetic fixture | P0 | pending | WELL-002 | project package and fixture | tests | no | Minimal implementation satisfies contracts | L | Focused pytest and Ruff pass |
| WELL-004 | Build thin Marimo explorer | P1 | pending | WELL-003 | `app.py` | validated package and fixture | no | Interactive evidence must not duplicate domain logic | M | Strict check and smoke test pass |
| WELL-005 | Add provenance, case study, and validation evidence | P1 | pending | WELL-004 | project documentation | passing project evidence | no | Recruiter claims must remain traceable | S | Claim and provenance review pass |

## Completed

| id | completed | evidence |
|---|---|---|
| WELL-001 | 2026-07-29 | Approved specification |
