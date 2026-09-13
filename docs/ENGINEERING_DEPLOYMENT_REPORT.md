# Deployment Readiness Report — AcademicCheck AI

Date: 2026-09-07  
Score (production readiness): **82 / 100**. Gate 98. **Fail.**

## Docker

- `docker-compose.prod.yml`: API, worker, PgBouncer (declared).
- `docker-compose.cert.yml`: Postgres 16 `:55432`, Redis 7 AOF `:56379`.
- Image build + CVE scan: **not run** this pass.

## CI/CD

`.github/workflows/ci.yml`:

- Backend: ruff, pytest cov 70, critical 75, AI/a11y/reliability tests.
- Frontend: tsc, axe, Playwright a11y (port 3100).
- `pip-audit || true` — **does not block**.
- Duplicate Playwright `env:` block removed this pass (invalid YAML / last-wins).
- No deploy job, no migration job, no image publish.

## Secrets / environments

- `assert_deployable_secrets()` on startup.
- Optional `SECRETS_FILE` JSON allow-list (`app/core/secrets.py`); env wins.
- `.env` must not be committed.
- Staging vs production: code paths exist (`is_staging` admin docs; production SQLite forbidden). Distinct hosted staging/production: **not proven here**.

## Migrations / rollback

- Alembic head **007**.
- Production lifespan does **not** `create_all`.
- Migration rollback drill: **not run** (`docs/DEPLOYMENT_CERTIFICATION.md`).
- Local blue-green: workstation proxy `ops/cert_bluegreen_results.json` (green kill → blue). Nginx/K8s/canary: **not run**.

## Restore

`ops/cert_restore_audit.json`: local Docker dump/restore, RTO 21.317 s, row counts matched for 100k assignments / 1M findings. `managed_postgres: false`. WAL PITR **not** exercised.

## Remaining go-live blockers (infra)

1. Secret manager (not a file on disk).
2. Managed Postgres + PITR.
3. Image scan + pinned deploys.
4. Staging with `REQUIRE_QUEUE=true` and registered workers on `/api/ready`.
5. Hosted rollback rehearsal.

## Verdict

Compose files and CI unit/a11y gates exist. Deployment is **not** production-certified. Local blue-green is not a cloud LB certificate.
