# Database recovery runbook

Target RPO: 5 minutes with managed PostgreSQL PITR enabled.  
Target RTO: 60 minutes for a staging restore drill.

These targets are **design goals**. They are not certified until the drill below is executed against a **managed** instance.

Local Docker evidence (not a cloud SLA): five `pg_restore` cycles, fingerprints matched, RTO **21.317 s**, `managed_postgres: false`. See `docs/DISASTER_RECOVERY_REPORT.md` and `ops/cert_restore_audit.json`.

## Provision

1. Create managed PostgreSQL 16 (or later) with encryption at rest and automated backups.
2. Set `DATABASE_URL` to that instance. Production refuses SQLite.
3. Run `alembic upgrade head` from `backend/`.
4. Confirm revisions `002` and `003` applied.

## Backup

```bash
bash ops/backup_postgres.sh
```

Keep the dump off the API host. Enable PITR on the provider console (`ops/PITR.md`).

## Restore drill

1. Snapshot current row counts for assignments, documents, analysis_reports, credits, payments, subscriptions, analysis_jobs.
2. Delete a disposable test tenant’s rows only.
3. Restore with `bash ops/restore_postgres.sh`.
4. Re-count the same tables. They must match the snapshot.
5. Log in as that tenant and open one assignment, document, report, and billing page.

## Certification

A restore that has not been executed is not a restore. File the counts in `docs/RECOVERY_VALIDATION.md`.
