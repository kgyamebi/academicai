# Recovery Objectives — AcademicCheck AI

Date: 2026-09-07  
Rule: **design** targets are not SLAs. **Measured** values cite `ops/cert_*.json` only. Empty measured cells mean **not measured** — not “probably fine.”

Design targets below are copied from `ops/PITR.md` / `docs/RECOVERY_RUNBOOK.md` where they existed. They are **unmet** until a managed drill exists.

## How to read this table

- **RTO measured:** wall time of a restore or process recover on the cert host. Not a cloud SLA.
- **RPO measured:** what can actually be recovered after the failure that was tested.

| Service | Design RTO | Design RPO | Measured RTO | Measured RPO | Status |
| --- | --- | --- | --- | --- | --- |
| PostgreSQL | 60 min staging / 2 h cutover (`ops/PITR.md`) | 5 min if PITR | **51.981 s** restore after destroy (`cert_restore_audit.json` 2026-09-09 `rto_s`) | Last custom `pg_dump` only | Local dump **PASS**. PITR **FAIL** |
| Redis | not formally set | AOF fsync policy unset in docs | Docker restart PONG (`cert_redis_restart.json`) + chaos ready recover | Volume retained; wipe **unsigned** | Process restart **PASS**. Volume-loss AOF **unrun** |
| Object storage | not set | not set | Local checksum restore (`cert_storage_recovery.json`) | Last sidecar tree | Local fixture **PASS**. S3/R2 **FAIL unrun** |
| Workers | not set | jobs durable in Redis/DB | Kill drill: replacement worker; **1/12 stuck** (`cert_worker_death.json`) | DB job row remains; RQ payload may stick | **FAIL** zero-stuck |
| Uploads (document bytes) | not set | not set | **not run** | DB `documents` row ≠ file | **FAIL** |
| Reports (DB) | follow Postgres | follow Postgres | Restored `analysis_reports` 1101 (`cert_restore_audit.json`) | Last dump | Local **PASS** with Postgres |
| Reports (PDF/export files) | not set | not set | **not run** as restore | Regenerable from DB in principle; **not drilled** | **unrun** |
| Billing (ledger rows) | follow Postgres | follow Postgres | Restored payments/credits/subscriptions count **1** each (cert seed, not live ledger) | Last dump; PSP is source of money truth | Local rows **PASS**. Live PSP **FAIL** |
| Authentication (users/sessions in DB) | follow Postgres | follow Postgres | Restored `users` 6 | Last dump; JWT secrets **not** in dump | Rows **PASS**. Secret restore **FAIL** (DR-07) |
| AI services | degrade immediately | n/a (stateless) | Heuristic load only (`live_provider: false`) | No AI state in DB required for core scores | Code path exists; **live kill unrun** |

## Validation of objectives

| Objective | Validated? | Why |
| --- | --- | --- |
| Local logical RTO ~52 s (2026-09-09) | **Yes** on cert host, that dataset | Do not quote as production RTO |
| RTO 60 minutes managed | **No** | No managed instance drill |
| Storage local checksum RPO | **Yes** for fixture drill only | Not S3 |
| RPO 5 minutes (PITR) | **No** | WAL not replayed |
| Billing RPO = PSP | **Unproven live** | Keys absent |
| Storage RPO (S3/CRR) | **No** | No object backup offsite |

Do not publish these design numbers as customer SLAs.
