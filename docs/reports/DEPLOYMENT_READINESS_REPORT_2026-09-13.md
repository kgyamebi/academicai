# Deployment Readiness Report

**Product:** AcademicCheck AI (public free launch · billing disabled)  
**Date:** 2026-09-13  
**Checklists:** `docs/PUBLIC_FREE_LAUNCH_GO_LIVE.md`, `docs/FAILURE_RECOVERY_CHECKLIST.md`  

## Verdict

| Metric | Score | Gate |
| --- | ---: | --- |
| Evidence-backed deployment readiness | **74 / 100** | **98 FAIL** |

**Go-live on staging/production host: NOT READY** under the 98 gate.

## Measured this pass

| Item | Result |
| --- | --- |
| `STAGING_URL` env | **absent** |
| `SENTRY_DSN` / `NEXT_PUBLIC_SENTRY_DSN` | **absent** |
| Local API + web up | live/ready/metrics/frontend **200** |
| Local ready semantics | DB ok; **Redis false**; **workers null**; still ready in **development** |
| GHA rollback drill | Requires `secrets.STAGING_URL` — historically fail-closed when unset |
| Local blue-green proxy | Prior pass `ops/cert_bluegreen_results.json` pass=true; cloud LB **not_run** |
| Billing | Intentionally disabled — checkout not a deploy blocker for free launch |

## Findings

| ID | Severity | Finding | Status |
| --- | --- | --- | --- |
| DEP-S1 | **Critical** | No staging URL to verify deploy | Open |
| DEP-S2 | **High** | Monitoring (Sentry) not active in this environment | Open |
| DEP-S3 | **High** | Worker/Redis not proven on a hosted ready probe | Open |
| DEP-S4 | **High** | Backup/PITR on managed Postgres unproven | Open |
| DEP-S5 | Medium | Rollback drill not executed against real staging | Open |

## Path to 98 (measurable)

Complete `docs/PUBLIC_FREE_LAUNCH_GO_LIVE.md` with every box checked and attach:

1. Staging URL (HTTPS)  
2. `/api/live` + `/api/ready` JSON snapshots (redis+workers)  
3. Sentry event ID from intentional test error  
4. Worker process list / queue depth  
5. Backup + restore timestamps  
6. Rollback drill log (GHA or runbook)  
7. E2E smoke log (register → check → report → return)

## Sign-off

Deployment 98+: **NO**  
Signed: _pending staging cutover evidence_
