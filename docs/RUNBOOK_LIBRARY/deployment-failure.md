# Runbook: Failed deployment

**SEV:** 2 if staging/prod unhealthy after ship; 1 if irrecoverable schema; 0 if deploy caused data loss.  
**Owner:** DevOps (unassigned).  
**Evidence:** Local blue-green `ops/cert_bluegreen_results.json`. Cloud CD **not wired**. `deploy-rollback-drill.yml` fail-closed without `STAGING_URL`.

## Detection

- Ready 503 on the new color
- 5xx spike after shift
- Workers 0
- Migration error

## Impact

Users on a broken SHA. Possible schema drift (OPS-15).

## Mitigation

Stop shipping. Do not roll forward billing/auth fixes without IC. Health gate is `/api/ready`, never `/api/live` alone.

## Recovery

1. Shift to previous color/image (`docs/DEPLOYMENT_OPERATIONS_GUIDE.md`).
2. Migrations: restore dump, not `alembic downgrade` on tenant data.
3. CI green is necessary not sufficient (cov 70/75, not 90).
4. Image scan: **not run** (OPS-10).

## Escalation

SEV-2. Emergency change: IC approval (`docs/CHANGE_MANAGEMENT_MANUAL.md`).

## Validation

Ready 200, workers registered, no 5xx spike vs pre-change (process-local caveat).

## Postmortem

SEV ≥ 2. Include SHA, alembic head, rollback yes/no.
