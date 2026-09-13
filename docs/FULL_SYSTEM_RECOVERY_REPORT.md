# Full System Recovery Report — AcademicCheck AI

Date: 2026-09-07  
Combined simultaneous failure: **not run** (`docs/DISASTER_RECOVERY_DRILL_REPORT.md`).

This report composes **separate** laboratory drills. That is weaker than a single timed runbook execution.

## Intended recovery order (design — not timed as a unit)

1. Secrets / config (unproven restore — DR-07)
2. PostgreSQL volume or dump → scratch validate → cut over
3. Object storage (unproven)
4. Redis (process or AOF — AOF unproven)
5. API (`/api/ready` 200) then workers
6. DNS/TLS (unrun)
7. PSP webhooks (keys absent)

Do not start workers before Postgres+Redis accept connections if `REQUIRE_QUEUE=true`.

## Drills (individual)

| Simulation | Run? | Integrity | Service restoration |
| --- | --- | --- | --- |
| Database loss (logical scratch) | **Yes** dump/restore | counts + id-fingerprints match | API not recertified as part of that restore |
| Redis loss (process stop) | **Yes** chaos | Job inventory **not** measured | live 200, ready 503 → 200 |
| Storage loss | **No** | — | — |
| Worker loss | **Yes** kill | **1 stuck / 12** | Replacement worker started |
| Application loss (green kill) | **Yes** local blue-green | HTTP 0 errors on proxy | Rollback to blue |
| Combined (all at once) | **No** | — | — |

Artifacts: `ops/cert_restore_audit.json`, `ops/cert_chaos_results.json`, `ops/cert_worker_death.json`, `ops/cert_bluegreen_results.json`.

## Data vs system integrity

| Layer | After individual drills |
| --- | --- |
| Postgres tenant tables | Match dump (local) |
| Document **files** | Not in dump — **unrecovered by DB drill** |
| Redis jobs | Unknown across volume loss; 1 stuck across worker kill |
| Billing vs PSP | Unlinked (no keys) |
| JWT secrets | Not in dump |

## Verdict

**FAIL** full-system recovery certification.  
**PASS** only as a set of isolated local drills. Recovery order above is a procedure, not a measured timeline.
