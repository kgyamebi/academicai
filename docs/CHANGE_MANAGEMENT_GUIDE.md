# Change Management Guide — AcademicCheck AI

Date: 2026-09-07  
Full workflows: `docs/CHANGE_MANAGEMENT_MANUAL.md`. This file is the short checklist.

Production CD is **not implemented**. Using these checklists on localhost does not certify enterprise change management.

## Release approval

| Environment | Approver | Gate |
| --- | --- | --- |
| Development | Author | Tests locally |
| CI | Automated | ruff, pytest cov≥70, isolation/billing 75, a11y, AI quality |
| Staging | Backend + SRE (unassigned) | `STAGING_URL` `/api/ready` 200; workers registered; `REQUIRE_QUEUE=true` |
| Production | Incident commander + payments (unassigned) | Staging soak, live billing artifact, restore artifact, pentest |

GitHub: PR review + CI. No prod deploy job. `pip-audit` does **not** block.

## Deployment checklist

1. CI green on the merge SHA.
2. Secrets from manager / `SECRETS_FILE` — not git (`.env` ignored).
3. `APP_ENV` staging/production — not sqlite.
4. Alembic at head **007** recorded in the change log.
5. Image digest pinned (scan **not run** — note residual OPS-10).
6. Health gate: `/api/ready` 200, not only `/api/live`.
7. Workers ≥ 1, queue depth finite.
8. Rollback image identified **before** shift.

## Rollback checklist

1. Shift traffic to previous color/image (`docs/RUNBOOK_LIBRARY/deployment-failure.md`).
2. Config: previous secrets; `JWT_SECRET_PREVIOUS` if mid-rotation (`ops/rotate-secrets.md`).
3. Schema: **restore dump**, do not `alembic downgrade` on tenant data.
4. Confirm ready 200 and no webhook storm.
5. Log the rollback in `ops/CHANGE_LOG.md`.

## Migration checklist

1. Backup / snapshot **before** migrate.
2. Expand-only preferred; inspector-safe index creates (004–007).
3. Run `alembic upgrade head` on staging first.
4. Verify row counts if a data backfill exists (none required for 007).
5. Forbidden: `001` `drop_all` on prod; `create_all` in production lifespan (already skipped).

## Emergency change

SEV-1/2 only. IC verbal/written approve. Same rollback plan. Postmortem required even if the emergency “worked.”

## Production change log

Append-only: `ops/CHANGE_LOG.md`. No production deploys are recorded yet — that is accurate, not a gap to paper over.
