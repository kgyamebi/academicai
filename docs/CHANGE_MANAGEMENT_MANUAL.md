# Change Management Manual — AcademicCheck AI

Date: 2026-09-07  
Short checklists also live in `docs/CHANGE_MANAGEMENT_GUIDE.md`. Production CD is **not implemented**. Following this manual on localhost does not certify enterprise change management.

Change log (append-only): `ops/CHANGE_LOG.md` — **no production rows**.

Approvers listed are roles (unassigned).

## Production change workflow

1. Ticket or PR states: service, SEV if incident-driven, rollback plan, migration yes/no.
2. CI green on the merge SHA (`.github/workflows/ci.yml`: ruff, pytest cov≥70, isolation/billing 75, a11y, AI quality gate).
3. `pip-audit` is **non-blocking** (OPS-16). Record residual CVEs in the change ticket.
4. Staging (when `STAGING_URL` exists): `/api/ready` 200, workers ≥ 1, `REQUIRE_QUEUE=true`. Today the rollback drill **exits 1** without that secret.
5. Production approval: IC + payments if billing/auth/schema; otherwise backend + SRE.
6. Execute deployment checklist.
7. Monitor (process metrics + ready probe). Grafana **not deployed**.
8. Log the change in `ops/CHANGE_LOG.md`.
9. If fail: rollback checklist, then incident if user-visible.

## Release approval workflow

| Environment | Approver | Gate | Evidence today |
| --- | --- | --- | --- |
| Development | Author | Local tests | Informal |
| CI | Automation | Workflow above | Implemented |
| Staging | Backend + SRE | Ready + workers | **Blocked** — no `STAGING_URL` |
| Production | IC + payments | Staging soak, live billing artifact, restore artifact, pentest | **All missing** |

Forbidden: deploying with sqlite `DATABASE_URL` in production (API raises). Forbidden: committing `.env`.

## Emergency change workflow

Allowed only for **SEV-0/1/2** active incidents.

1. IC states the emergency in the incident issue (what, why skip staging).
2. Same rollback plan as a normal change, written **before** the ship.
3. Pair if possible (vacant roster → IC still records who typed).
4. Health gate `/api/ready` still required unless the change **is** the database restore (then validate on scratch first).
5. Postmortem required even if the emergency “worked.”

## Migration approval workflow

1. Backup / snapshot **before** migrate (OPS-26: backup is not metered).
2. Expand-only preferred. Index migrations 004–007 are inspector-safe creates.
3. `alembic upgrade head` on staging first. Head expected **007**.
4. Production migrate during a change window with IC aware.
5. Rollback = **restore dump**, not `alembic downgrade` on tenant data (`docs/RUNBOOK_LIBRARY/restore-failure.md`).
6. Forbidden: replay `001` `drop_all` / `create_all` on prod. Production lifespan already skips `create_all`.

## Deployment checklist

1. CI green on the SHA.
2. Secrets from manager / `SECRETS_FILE` — not git.
3. `APP_ENV` staging/production.
4. Alembic head recorded.
5. Image digest pinned (CVE scan **not run** — OPS-10).
6. `/api/ready` 200 on the new color **before** shift. Never gate on `/api/live` alone.
7. Workers ≥ 1, queue depth finite.
8. Rollback image identified before shift.
9. PSP keys: if taking paid traffic, `ops/cert_payment_keys.json` must not remain all-false in that environment.

## Rollback checklist

1. Shift traffic to previous color/image (`docs/RUNBOOK_LIBRARY/deployment-failure.md`).
2. Config: previous secrets; `JWT_SECRET_PREVIOUS` if mid-rotation.
3. Schema: restore dump to scratch, validate, then cut over.
4. Confirm ready 200; watch webhook unmatched (process counter, replica-local).
5. Log rollback in `ops/CHANGE_LOG.md`.
6. Open/update incident if users saw errors.

## Types that are not “standard changes”

| Type | Process |
| --- | --- |
| Feature flags / product UX | Out of scope for this ops pack — do not sneak product work into an emergency change |
| Live credit grant | Forbidden in SQL. PSP dashboard + `apply_refund` / existing apply path only |
| Secret rotation | `ops/rotate-secrets.md` as a planned change unless SEV-0 leak |
