---
title: Public Engineering Portfolio Backlog
status: active
last_updated: 2026-07-30
---

# Backlog

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
|---|---|---|---|---|---|---|---|---|---|---|
| PORT-PUB-001 | Establish clean-root domain, product intent, rights boundary, and cycle plan | P0 | completed | - | repository policy and specs | approved parent Discovery | no | Implementation needs committed clean authority | S | Spec and plan checks pass |
| PORT-PUB-002 | Build synthetic wellness data pipeline | P1 | completed | PORT-PUB-001 | `projects/wellness-data-pipeline/` | public portfolio spec | yes | Generalized data-engineering competency evidence | L | 34 tests and browser gates pass |
| PORT-PUB-003 | Build content performance classifier | P1 | completed | PORT-PUB-001 | `projects/content-performance-classifier/` | approved classifier spec | yes | Generalized data-science and SEO evidence | L | 27 tests and browser gates pass |
| PORT-PUB-004 | Build public-sector opportunity pipeline | P1 | completed | PORT-PUB-001 | `projects/public-sector-opportunity-pipeline/` | approved opportunity-pipeline spec | yes | Prefect and forward-deployed integration evidence | L | 66 tests and browser gates pass |
| PORT-PUB-005 | Build recruiter/client landing page and project evidence packets | P0 | completed | PORT-PUB-002, PORT-PUB-003, PORT-PUB-004 | README, project pages, `site/` | validated projects and product links | no | Claims must follow evidence | M | Claim, keyboard, semantics, link-target, and mobile reflow gates pass |
| PORT-PUB-006 | Add reproducible environment and CI | P0 | completed | PORT-PUB-002 | manifests, locks, scripts, workflow | all project validation | no | Fresh clones and public exports need one authority | M | Locked tests, strict checks, WASM, Chromium, scan, and SBOM workflow prepared |
| PORT-PUB-007 | Prepare local release preview | P0 | completed | PORT-PUB-005, PORT-PUB-006 | release evidence | clean branch and old remote | no | Remote replacement remains approval-gated | S | Exact local SHA and publication boundary recorded |
| PORT-PUB-008 | Publish reviewed clean root and enable Pages | P0 | completed | PORT-PUB-007 | canonical GitHub repository and initial Pages deployment | approved local preview | no | Owner approved clean-history replacement | S | Remote source SHA, CI, initial Pages deployment, and rollback evidence passed |
| PORT-PUB-009 | Retire Pages and make GitHub plus Molab the public interface | P0 | active | PORT-PUB-008 | README, workflow, static-site retirement, provenance | published source and notebook audit | no | GitHub-only portfolio removes duplicate stale surface | M | Repository-only contract, CI, Molab links, Pages 404, and draft PR pass |
| PORT-PUB-010 | Build clean-room WordPress migration workbench | P1 | pending | PORT-PUB-009 | new spec and project | only generalized migration concepts | yes | Strong fixed-scope service evidence without client reuse | L | Synthetic export, pure transforms, dry-run manifest, tests, and Molab pass |
| PORT-PUB-011 | Build clean-room media-to-CMS delivery simulator | P2 | pending | PORT-PUB-009 | new spec and project | only generalized YouTube/CDN/CMS concepts | yes | Useful integration evidence after contract redesign | L | Synthetic adapters, retry/idempotency contracts, Prefect parity, and Molab pass |
| PORT-PUB-012 | Reassess restaurant-location data-quality app | P2 | blocked | PORT-PUB-009 | independent dataset provenance and new project | no legacy outputs or unknown-license data | yes | Best low-effort historical analytical concept | M | Cleared data or synthetic fixture, tests, conclusions, and Marimo pass |

## Completed

| id | completed | evidence |
|---|---|---|
| PORT-PUB-001 | 2026-07-29 | Empty-history branch and approved clean-root artifacts |
| PORT-PUB-002 | 2026-07-29 | 34 tests, strict Marimo, executed WASM, and Chromium interaction |
| PORT-PUB-003 | 2026-07-29 | 27 tests, leakage and privacy gates, executed WASM, and Chromium interaction |
| PORT-PUB-004 | 2026-07-29 | 66 tests, incremental and orchestration gates, executed WASM, and Chromium interaction |
| PORT-PUB-005 | 2026-07-29 | Responsive recruiter/client landing page and current evidence packets |
| PORT-PUB-006 | 2026-07-29 | Locked multi-project quality and Pages workflow |
| PORT-PUB-007 | 2026-07-29 | Local preview prepared; no remote replacement or deployment |
| PORT-PUB-008 | 2026-07-29 | Owner-approved clean-root history published at `0a07de7`; recovery bundle and ref retained |
