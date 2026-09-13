# Deployment Gap Report — AcademicCheck AI

Date: 2026-09-07  
Production readiness remains **82 / 98**.

| Item | Status | Evidence |
| --- | --- | --- |
| Docker | Compose files exist | `docker-compose.yml`, `.prod.yml`, `.cert.yml` |
| Image scan | FAIL | Not run |
| CI | PARTIAL | Tests + a11y; `pip-audit \|\| true`; no deploy |
| CD | FAIL | No production pipeline |
| Rollback | PARTIAL | Local proxy drill; not Nginx/K8s |
| Blue-green | PARTIAL | Workstation only (`cert_bluegreen_results.json`) |
| Backups | PARTIAL | Local dump/restore |
| Environment separation | PARTIAL | Code paths; hosted staging/prod unproven |
| Secrets management | FAIL | Env / optional JSON file |
| Alembic | PARTIAL | Head 007; 001 still create_all history |
| Staging workers | FAIL | Not proven |

**Production deployment requirements are not satisfied.**
