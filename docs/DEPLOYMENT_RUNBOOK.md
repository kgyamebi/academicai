# Deployment Runbook — AcademicCheck AI

## Promotion (intended)

1. CI green: ruff, pytest cov≥70, isolation/billing floors, pip-audit non-blocking.  
2. Staging with managed Postgres, Redis, workers, `SECRETS_FILE` or secret manager, `REQUIRE_QUEUE=true`.  
3. Restore drill on staging (`docs/DISASTER_RECOVERY_PLAN.md`).  
4. Production only after live billing and pentest artifacts exist.

This environment has **not** completed steps 2–4.

## Blue-green

Workstation proxy: `ops/cert_bluegreen.py` — green 20/20, kill green, rollback to blue, 0 errors. Cloud LB / k8s / canary percent: **not run**.

## Rollback

- App: previous image / task definition. Local automatic rollback proven.  
- Config: re-inject previous `SECRETS_FILE` / env; JWT previous key if mid-rotation.  
- Migration: restore from dump — **not** `alembic downgrade` certified.

## Health

LB must use `/api/ready`, not `/api/live`. Live stays 200 during Redis/Postgres death by design.

## Approval

No deployment approval workflow is implemented in GitHub beyond CI. Treat as **FAIL** for enterprise change-management.
