# Disaster Recovery Risk Register — AcademicCheck AI

Date: 2026-09-09  
Rule: risks come from restore/chaos/queue JSON, compose files, and code. Unrun drills are not green.  
Disaster recovery score **86 / 98**. Production DR still **FAIL**.

Related ops risks: OPS-03 (PITR), OPS-07 (stuck job), OPS-09 (guest purge), OPS-14 (chaos gaps), OPS-26 (backup not metered).

| ID | Risk | Area | Class | Evidence | Residual |
| --- | --- | --- | --- | --- | --- |
| DR-01 | No managed PITR | PostgreSQL | **Critical** | `ops/cert_restore_audit.json` `managed_postgres: false`; RPO = last `pg_dump` | Writes after dump are unrecoverable |
| DR-02 | WAL archive persist vs PITR replay | PostgreSQL / compose | **Critical** | Volume `postgres_wal_archive:/backups` added 2026-09-07 so `archive_command` is not discarded on container replace. **WAL replay still unrun.** Cert compose already had `cert_pg_backups` but no `archive_command`. | Files on disk ≠ point-in-time restore |
| DR-03 | Backups not scheduled offsite | Backup | **Critical** | `ops/backup_postgres.sh` exists. `.github/workflows/backup-postgres.yml` **exits 1** without secrets | Silent/unuploaded dump |
| DR-04 | Object bytes not in DB dump | Storage / documents | **Critical** | Restore restored `documents` **rows** (6); `cert_storage_results.json` is local-disk throughput, not restore | Essay files lost if disk/bucket gone |
| DR-05 | S3/R2 restore unrun | Storage | **Critical** | `not_run`: s3, r2; chaos `storage_kill` not_run | No object recovery procedure proven |
| DR-06 | Live PSP recovery unrun | Billing | **Critical** | `ops/cert_payment_keys.json` all false | Cannot prove no double-charge in production |
| DR-07 | Secrets have no restore path | Secrets | **Critical** | Env / `SECRETS_FILE`; no manager snapshot | JWT/PSP keys unrecoverable after host loss |
| DR-08 | Full-system combined drill unrun | Infrastructure | **Critical** | `docs/DISASTER_RECOVERY_DRILL_REPORT.md` simultaneous = not run | Recovery order unproven |
| DR-09 | Redis AOF restore unsigned | Redis / queue | **High** | AOF on in cert/prod compose; no `BGREWRITEAOF` / copy / replay cert JSON | Queue replay after volume loss unknown |
| DR-10 | Worker SIGKILL leaves stuck job | Workers | **High** | `ops/cert_worker_death.json` stuck=1, `pass: false` | Orphan until 900s reaper |
| DR-11 | Fingerprints are not full-row hashes | Database validation | **High** | `ops/cert_restore_audit.py` hashes COUNT+MIN(id)+MAX(id) | Silent in-place UPDATE corruption would still “match” |
| DR-12 | Two dump formats | Backup automation | **High** | Cert: custom `pg_dump --format=custom`. Script: `pg_dump \| gzip` + `psql` restore | Operators can restore the wrong tool |
| DR-13 | Encrypted-at-rest dump unproven | Data protection | **High** | Backup validation: encrypted backup **not used** | Dump theft = full PII/ledger |
| DR-14 | Region / multi-AZ unrun | Cloud | **High** | No second region, no DNS failover drill | Cloud-region loss = unmeasured RTO |
| DR-15 | CI cannot restore | CI/CD | **High** | CI uses sqlite; no restore job | Backups never validated in pipeline |
| DR-16 | AI live failover unrun | AI | **Medium** | `ops/cert_ai_results.json` `live_provider: false`; chaos `ai_provider_kill` not_run | Heuristic path is code, not a live drill |
| DR-17 | Auth sessions vs Redis | Authentication | **Medium** | Prod rate-limit needs Redis; JWT in Postgres | Redis loss ≠ session table loss, but login 503 |
| DR-18 | Reports vs findings coupling | Reports | **Medium** | Findings drop recovered via dump (cert); report **files**/PDF not in dump | PDF regenerate from DB possible; original upload still DR-04 |
| DR-19 | Queue 5k–50k analysis unrun | Queues | **Medium** | 1000 analysis pass; 50k ping not completed | Recovery under overflow unknown |
| DR-20 | PgBouncer is a restore SPOF | App servers | **Low** | API uses bouncer in prod compose | Restart bouncer; data still on Postgres volume |
| DR-21 | RQ vs Celery confusion | Queues | **Low** | Worker is RQ | Wrong restore mental model |

## Recovery bottlenecks (manual)

1. Human runs `pg_dump` / `pg_restore` (GHA backup job fail-closes without secrets).
2. Human must know custom vs gzip format (DR-12).
3. Object restore has no script.
4. PSP disputes need dashboards this repo does not have.
5. Secret reconstitution is tribal knowledge (`ops/rotate-secrets.md` is rotation, not backup).

## Recovery SPOFs

| SPOF | If it dies | Proven recovery |
| --- | --- | --- |
| Single Postgres volume | All tenant + billing rows | Local dump to **scratch** DB only |
| Single Redis volume | Queue + prod rate-limit | Process restart (chaos); AOF replay **unproven** |
| Single local disk / one bucket | Uploads | **None** |
| Vacant on-call | Who runs restore | **None** (OPS-01) |
| Single region (undeclared) | Everything | **None** |

## What is proven (do not over-read)

Local Docker Postgres 16, 2026-09-07T09:49:43Z: five `pg_restore` cycles, counts match, id-fingerprint match, accidental DELETE / DROP findings / failed migration / dropdb recovered. That is **not** production DR.
