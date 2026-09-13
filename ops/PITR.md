# Point-in-time recovery

Date: 2026-09-09

## What is proven locally

WAL archive + `recovery_target_time` against Postgres 16 Alpine (`ops/docker-compose.pitr.yml`).

Artifact: `ops/cert_wal_pitr.json` (two consecutive runs).

| Run | Target timestamp | Before restore | After PITR | Result |
| --- | --- | --- | --- | --- |
| 1 | 2026-09-09 21:11:06.475717+00 | ids 1,2 | id **1** only (`before-target`) | PASS |
| 2 | 2026-09-09 21:11:58.47254+00 | ids 1,2 | id **1** only | PASS |

This is the same engine mechanism a managed provider uses. It is **not** a certificate that RDS/Neon/Cloud SQL PITR works in our account.

## Local runbook

```bash
docker compose -f ops/docker-compose.pitr.yml up -d
py -3.14 ops/cert_wal_pitr.py
# Expect ops/cert_wal_pitr.json pass=true, ids_after_pitr=1 both runs
docker compose -f ops/docker-compose.pitr.yml down -v
```

Do not point this compose at cert/prod data volumes.

## Managed provider (pending live account)

1. Enable PITR / WAL retention ≥ 7 days on the vendor console.
2. Quarterly: restore snapshot + WAL to T-15 minutes on a **scratch** instance (never primary).
3. Compare `users` / `payments` / `analysis_reports` counts to a pre-drill manifest.
4. Record the vendor restore job ID in the ops channel.

RPO target (design): 5 minutes with managed WAL. Local dump RPO remains “time since last `pg_dump`”.

## Cutover

Expand schema with Alembic on the restored scratch if needed. Never `alembic downgrade` on customer data. Never restore onto the production primary.
