# Point-in-time recovery

Use the managed PostgreSQL provider's PITR. Do not invent a custom WAL shipper in application code.

## Architecture

- Primary: managed Postgres with WAL retention ≥ 7 days
- Backups: nightly `ops/backup_postgres.sh` to object storage + provider snapshots
- RPO target: 5 minutes (WAL)
- RTO target: 2 hours (restore to scratch, then cut over)

## Quarterly drill

1. Create a scratch instance.
2. Restore the latest snapshot + WAL to T-15 minutes.
3. Run `SELECT count(*) FROM users, payments, analysis_reports`.
4. Run the isolation pytest suite against the scratch API.
5. Record the drill in the ops channel. A drill that is not restored is not a backup.

## Cutover

Expand schema with Alembic before restore if the backup predates a migration. Never `alembic downgrade 001` on customer data.
