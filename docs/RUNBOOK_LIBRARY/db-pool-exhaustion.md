# Runbook — Database connection pool exhaustion

## Symptoms
- Elevated latency / intermittent 503 on `/api/ready`
- Logs: pool timeout, `QueuePool limit`, `connection timed out`
- Metrics: `academiccheck_db_pool_checked_out` near `db.pool.size + overflow`

## Diagnosis
1. `GET /api/metrics` → inspect `gauges.db.pool.*`
2. Check PgBouncer / Postgres `max_connections` and active sessions
3. Confirm worker count × `DB_POOL_SIZE` is not oversubscribed

## Resolution
1. Reduce API workers or `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` to fit PgBouncer
2. Kill long-running idle transactions if safe
3. Scale Postgres / raise pool only with headroom
4. Redeploy with `ops/deploy_compose.sh` after config change; verify `/api/ready`

## Escalation
SEV-2 → SEV-1 if payments or analysis fully unavailable. See `docs/INCIDENT_RESPONSE_PLAN.md`.
