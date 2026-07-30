---
title: Public Engineering Portfolio Backlog
status: active
last_updated: 2026-07-29
---

# Backlog

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
|---|---|---|---|---|---|---|---|---|---|---|
| PORT-PUB-001 | Establish clean-root domain, product intent, rights boundary, and cycle plan | P0 | completed | - | repository policy and specs | approved parent Discovery | no | Implementation needs committed clean authority | S | Spec and plan checks pass |
| PORT-PUB-002 | Build synthetic wellness data pipeline | P1 | ready | PORT-PUB-001 | `projects/wellness-data-pipeline/` | public portfolio spec | yes | Generalized data-engineering certification evidence | L | Unit, contract, notebook, and data-quality tests pass |
| PORT-PUB-003 | Build content performance classifier | P1 | pending | PORT-PUB-001 | `projects/content-performance-classifier/` | public portfolio spec | yes | Generalized data-science and SEO evidence | L | Baseline, leakage, evaluation, notebook, and fixture tests pass |
| PORT-PUB-004 | Build public-sector opportunity pipeline | P1 | pending | PORT-PUB-001 | `projects/public-sector-opportunity-pipeline/` | public portfolio spec | yes | Prefect and forward-deployed integration evidence | L | Idempotency, retry, schema, synthetic-fixture, and notebook tests pass |
| PORT-PUB-005 | Build recruiter/client landing page and project evidence packets | P0 | pending | PORT-PUB-002, PORT-PUB-003, PORT-PUB-004 | README, project pages, assets | validated projects and product links | no | Claims must follow evidence | M | Link, claim, accessibility, and responsive checks pass |
| PORT-PUB-006 | Add reproducible environment and CI | P0 | pending | PORT-PUB-002 | manifests and workflows | all project validation | no | Fresh clones and public exports need one authority | M | Matrix tests and strict checks pass |
| PORT-PUB-007 | Prepare local release preview | P0 | pending | PORT-PUB-005, PORT-PUB-006 | release evidence | clean branch and old remote | no | Remote replacement remains approval-gated | S | Preview identifies exact SHA, diff, rollback, and deployment plan |

## Completed

| id | completed | evidence |
|---|---|---|
| PORT-PUB-001 | 2026-07-29 | Empty-history branch and approved clean-root artifacts |

