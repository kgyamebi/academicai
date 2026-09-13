# Deployment Operations Report — AcademicCheck AI

Date: 2026-09-07  
Procedures: `docs/DEPLOYMENT_OPERATIONS_GUIDE.md`.  
Readiness remains **82 / 98**. This report does **not** certify production deploy.

| Mode | Validated? | Evidence |
| --- | --- | --- |
| Blue-green | **Partial** — workstation proxy | `ops/cert_bluegreen_results.json`: green 20/20, kill green, rollback blue, 0 errors. Nginx/Traefik/K8s **not run**. |
| Canary percent | **Fail** — not run | No canary controller |
| Rolling (K8s/ECS) | **Fail** — not run | Compose `api` + `worker` only |
| Rollback | **Partial** — local automatic | Same blue-green artifact; GHA `deploy-rollback-drill.yml` **exits 1** without `STAGING_URL` |
| Migration rollback | **Fail** — not certified | Restore-from-dump is the written procedure, not `alembic downgrade` |
| Health gate | **Specified + local** | Compose healthcheck hits `/api/ready`. Chaos: live 200 / ready 503 is correct. |

## Pipeline

- CI: `.github/workflows/ci.yml` (test/lint/a11y). No image publish.
- Drill workflow: refuses deploy without staging secret (fail-closed). That is a **control**, not a green CD.

## Residual

OPS-02, OPS-10, OPS-18, OPS-19. Do not take production traffic on compose files alone.
