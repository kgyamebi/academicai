# Launch recovery runbook — AcademicCheck AI

Operator-facing restore path for soft launch and production. Local Docker restore is evidenced; **managed PITR must still be proven on your host**.

## Objectives (targets)

| Asset | RTO target | RPO target | Status |
| --- | --- | --- | --- |
| PostgreSQL | &lt; 60 min staging / &lt; 2 h cutover | Last backup; PITR ≤ 5–15 min when enabled | Local dump restore proven; managed PITR open |
| Object storage | &lt; 2 h | Last object version / sync | Depends on S3/R2 config |
| Redis / RQ | &lt; 15 min | Jobs may requeue; not source of truth | Workers recover orphans on start |
| Secrets | &lt; 30 min | n/a | Restore from secret manager / offline escrow |

## Database backup

1. Prefer **managed automated backups** (Railway/Render/RDS/Cloud SQL) with point-in-time if available.
2. Additionally schedule encrypted dump:
   - `ops/backup_postgres.sh`
   - optional AES via `BACKUP_ENCRYPTION_KEY` (`ops/encrypt_backup_file.py`)
   - offsite copy: `ops/offsite_backup.py`
3. Verify: `ops/backup_verification.py` / `ops/validate_restore.py`

## Database restore (step-by-step)

1. Put the API in maintenance (scale workers to 0; stop writes).
2. Provision empty Postgres (or restore target instance).
3. Restore:
   - Managed console: restore snapshot / PITR to new instance, update `DATABASE_URL`.
   - Dump path: `ops/restore_postgres.sh` or `ops/restore_database.sh` against the dump artifact.
4. Run `alembic upgrade head` if the dump is pre-migration.
5. Start one API instance; confirm `/api/ready`.
6. Start workers; confirm orphan recovery logs.
7. Spot-check: login, open one assignment, open one report, download PDF.
8. Record: timestamp, backup ID, row-count check (`ops/cert_restore_audit.py` pattern).

## Redis recovery

1. Redis is a queue cache, not the system of record.
2. Restart Redis; start workers.
3. Stuck jobs: workers call `recover_and_requeue_orphans` on boot; ops may use `ops/recover_jobs.py`.
4. Expect some in-flight analyses to re-run; credits/jobs should remain consistent via DB state.

## Object storage recovery

1. If `STORAGE_BACKEND=s3`, restore bucket versioning / replica.
2. If local disk, restore `/data/storage` (or `STORAGE_LOCAL_PATH`) from backup.
3. Validate one document download and one re-extract.

## Provider outage procedures

| Provider | User impact | Action |
| --- | --- | --- |
| OpenAI / LLM | Heuristic analysis still runs | Keep serving; alert; disable enrichment if erroring hard |
| Stripe/Paystack/Flutterwave | Checkout fails | Hide purchase CTAs (`checkout_available`); do not take money |
| Email/SMTP | Verification/reset delayed | Console/log fallback in staging; page ops |
| Sentry | Blind to exceptions | Rely on structured logs + `ALERT_WEBHOOK_URL` |

## Expected recovery times (honest)

- Local Docker dump restore (lab): ~30–60 seconds (cert artifacts under `ops/`).
- Managed snapshot restore: typically 15–60 minutes depending on host.
- Full region failover: **not certified** until multi-region is designed.

## Related docs

- `ops/PITR.md`
- `docs/RECOVERY_RUNBOOK.md`
- `docs/WAL_PITR_RUNBOOK.md`
- `docs/PRODUCTION_DEPLOYMENT_CHECKLIST.md`
