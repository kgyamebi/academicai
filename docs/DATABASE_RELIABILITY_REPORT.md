# Database Reliability Report — AcademicCheck AI

Date: 2026-09-07  
Evidence: `ops/cert_chaos_results.json`, `ops/cert_restore_audit.json`, `backend/app/db/session.py`.

| Concern | Control | Validated? |
| --- | --- | --- |
| Connection pooling | pool 10 / overflow 20 / pre_ping / LIFO | Config; storm n=40 errors 0 (`cert_postgres_results.json`) |
| Connection limits | pool_timeout 30 | **Exhaustion drill not run** |
| Query timeouts | statement 30s, lock 10s, connect 3s | Source pytest; **long-query drill not run** |
| Transaction protection | `get_db` rollback | Pytest isolation |
| Retry logic | pool_pre_ping on checkout | Not a SQL retry loop |
| Liveness | `/api/live` 200 with PG down | Chaos **PASS** |
| Readiness | `/api/ready` 503 with PG down; recover 200 | Chaos **PASS** |
| Backup validation | dump + counts + id fingerprints | Local **PASS** |
| PITR | `ops/PITR.md` | **FAIL** not executed |
| Read replica | none | **FAIL** |
| Database restart | compose stop/start in chaos | **PASS** process restart |
| Database failover | managed failover | **FAIL unrun** |
| Lock contention | lock_timeout | **Deadlock inject unrun** |
| Migration rollback | restore dump not alembic downgrade | Restore audit failed-migration cycle **PASS** |

Cert path: API → Postgres **directly** (no PgBouncer). Prod compose has PgBouncer **unmeasured**.

## Verdict

Local restart + dump/restore **PASS**. Failover, PITR, exhaustion, deadlock load **FAIL**. Not a 98 DB reliability certificate.
