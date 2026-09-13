# Runbook: PostgreSQL down

**SEV:** 2 if ready 503 and live 200; **1** if writes failing globally; **0** if volume gone and last dump missing.  
**Owner:** Data (unassigned). **Alert:** A-DB (`academiccheck_database` = 0). Pager **unwired**.  
**Evidence:** Chaos 2026-09-07T12:36:39Z `postgres_down_ready` 503, recover 200.

## Detection

- `/api/ready` 503, JSON `database: false`
- Timeouts / 500s on mutations
- A-DB specified, not paged

## Impact

All authenticated product paths that hit the DB. Queue workers also fail. `/api/live` may remain 200.

## Mitigation

1. Do **not** point the API at SQLite.
2. Do **not** `DELETE`/`UPDATE` on primary without a ticket and a backup.
3. Fail closed: keep LB on `/api/ready` (503 is correct).

## Recovery

1. `pg_isready`; disk; connections; `statement_timeout` 30s / `lock_timeout` 10s.
2. Restart Postgres / PgBouncer if the process is dead.
3. If primary is gone: restore to **scratch** (`ops/restore_postgres.sh`), `ops/validate_restore.py`, then cut over.
4. Managed PITR: **not proven** (`managed_postgres: false`).

## Escalation

SEV-1 if restore required. SEV-0 if dump missing (OPS-03/26). IC vacant → detecting engineer.

## Validation

`/api/ready` 200. Row counts vs last dump (local restore audit matched 100k assignments / 1M findings **on cert Postgres only**).

## Postmortem

Required if SEV ≥ 2. Attach ready JSON, restore counts. Template: `docs/POSTMORTEM_TEMPLATE.md`.
