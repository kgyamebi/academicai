# Chaos Recovery Report — AcademicCheck AI

Date: 2026-09-09  

## Executed

| Chaos | When | Result | Artifact |
| --- | --- | --- | --- |
| Redis down → ready 503 → recover | 2026-09-07 | PASS | `ops/cert_chaos_results.json` |
| Postgres down → ready 503 → recover | 2026-09-07 | PASS | same |
| Redis container restart (AOF volume retained) | 2026-09-09 | PASS | `ops/cert_redis_restart.json` |
| DB delete / DROP / destroy + restore | 2026-09-09 | PASS | `ops/cert_restore_audit.json` |
| Local storage delete/corrupt + restore | 2026-09-09 | PASS | `ops/cert_storage_recovery.json` |

## Not run

| Chaos | Status |
| --- | --- |
| Storage kill (API path) | not_run |
| AI provider kill | not_run |
| Billing provider kill | not_run |
| Network partition | not_run |
| Deployment failure / bad image | not_run as chaos |
| Combined multi-component outage | not_run |

## Integrity

- After DB restore: counts + id fingerprints matched.
- After storage restore: SHA-256 inventory matched.
- User experience under chaos: fail-closed ready endpoint — **not** a full UX study.

## Verdict

**PARTIAL PASS** for Redis/Postgres process chaos + logical restore.  
**FAIL** full chaos recovery certification (provider/network/storage/combined).
