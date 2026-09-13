# Disaster Recovery Audit — AcademicCheck AI

Date: 2026-09-09  
Auditor roles: DR / SRE / Cloud / DBRE / DevSecOps / Platform / Security / BCP.  
Method: code + compose + ops scripts + cert JSON. Postgres restore audit **re-executed 2026-09-09T20:22:38Z** with FK orphan checks (`relationships_ok: true`).

**Production DR certified: NO.** Local/cert package: PASS for logical DB + local storage + Redis restart (see readiness assessment).

---

## Scope inventory

| Surface | Where it lives | Backup today | Restore proven? |
| --- | --- | --- | --- |
| PostgreSQL (users, assignments, documents metadata, reports, findings, jobs, payments, credits, subscriptions, versions) | `docker-compose.cert.yml` / prod compose / managed host (HAL) | `ops/backup_postgres.sh` (+ optional AES-GCM); GHA fails closed without secrets | **Local Docker YES (2026-09-09)**; managed PITR **NO**; prod dump/restore **AWAITING HUMAN** |
| Redis (RQ queues, rate-limit) | compose `appendonly yes` | Volume `redis_data` | Process restart **YES** (2026-09-09); AOF rebuild after volume loss / Sentinel **NO** |
| Workers (analysis/PDF/coach) | RQ + DB job rows | Job state in Postgres; RQ payload in Redis | Orphan recover **YES** (pytest); worker-kill stuck **FAIL** historically |
| File / object storage | Local disk default; S3-compatible optional | **No** scheduled object backup in prod | **Local delete/corrupt/restore YES** (`ops/cert_storage_recovery.json`); S3/CRR **NO** |
| Billing / webhooks / ledger | Postgres + PSP | Dump + reconcile CLI | Sandbox reconcile **YES**; live PSP **NO** |
| Monitoring | metrics + alert webhook/file | Config in git | Hosted scrape **NO** |
| Deployment | compose / image | git + prior image | Local blue/green cert exists; prod CD **unproven** |

---

## Gaps / SPOFs / risks

| ID | Class | Finding |
| --- | --- | --- |
| DR-01 | Critical | No managed PITR evidence |
| DR-02 | Critical | WAL archive volume exists; **replay unrun** |
| DR-03 | Critical | Scheduled offsite backup GHA exits without secrets |
| DR-04 | Critical | Object bytes not in `pg_dump` |
| DR-05 | Critical | S3/R2 versioning + cross-region **absent in evidence** |
| DR-06 | Critical | Live payment recovery unrun |
| DR-07 | Critical | Secrets not in dump; no secret-manager restore path |
| DR-08 | Critical | Combined full-system drill unrun |
| DR-09 | High | Redis AOF restore unsigned |
| DR-10 | High | Worker SIGKILL stuck residual (historical) |
| DR-11 | High | Fingerprints are not full-row hashes | Open — FK orphan checks now **PASS**; in-place UPDATE still would match |
| DR-12 | High | Dual dump formats (custom vs gzip) |
| DR-13 | Medium→Reduced | Encrypted dump **now implemented + locally proven**; prod key+offsite still open |
| DR-14 | High | No secondary region |
| DR-15 | High | CI does not restore Postgres (sqlite) |

---

## Dependency risks

- API `REQUIRE_QUEUE=true` → Redis + workers required for analysis path.
- Billing truth = PSP + internal ledger; dump alone is insufficient after webhook loss.
- Auth JWT signing keys are not in the database dump.
- Documents: DB row without object bytes = broken download.

## Business continuity risks

- Vacant on-call (HAL-11).
- No public status page.
- Region loss RTO **unbounded**.
- Paid traffic must halt on ledger/PSP mismatch (policy exists; live drill open).

## This pass closed (engineering only)

- Encrypted backup crypto + verification CLI
- Local object storage recovery drill (checksummed)
- `recover_jobs.py`, `reconcile_billing.py`, `restore_database.sh`, `dr_local_drill.py`
- Docs package refresh (this file and related certifications)

## Verdict

**Audit: FAIL for production launch DR.**  
**Partial PASS for local logical DB (historical) + local storage recovery + backup encryption round-trip (this pass).**
