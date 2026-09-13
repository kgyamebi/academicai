# Production Readiness Report

Date: 2026-09-07  
Previous score: 78. **Evidence-backed score: 82 / 100.** Gate 98. **Fail.**

| Item | Current state | Fix this pass | Evidence | Remaining risk |
| --- | --- | --- | --- | --- |
| Docker | `docker-compose.prod.yml` + `docker-compose.cert.yml` | Cert PG/Redis actually started | `docker compose ps` healthy | Images not built/scanned |
| CI/CD | ruff, pytest, tsc, axe | unchanged | `.github/workflows/ci.yml` | Lighthouse not default |
| Monitoring | `/api/metrics` | unchanged | health.py | No Prometheus/Grafana |
| Tracing | none | **not added** | — | No distributed traces |
| OpenTelemetry | not installed | not installed | `docs/OBSERVABILITY_CERTIFICATION.md` | No collector |
| Backups / restore | local `pg_dump`/`pg_restore` | executed | `ops/cert_restore_results.json` pass | Not managed PITR |
| Workers | RQ SimpleWorker on Windows, fork on POSIX | 1000 jobs | `ops/cert_queue_results.json` | 5k–50k unrun; no HA workers |
| Ready hang on dead Postgres | TCP wait | `connect_timeout=3` | chaos postgres_down_ready **503** | Pool still 30s for in-flight checkouts |
| Indexes | 004/005 + **006** | citations/references/analytics composites | EXPLAIN after | Analytics GROUP 100k still ~50–125 ms |
| Secrets | prod rejects weak JWT | unchanged | `assert_deployable_secrets` | Not in a secret manager |
| Load / HA | one workstation | k6 100 VU | p95 **fail** 1.87 s | 50k users unrun; SPOF remains |

## Decision

**Not production-ready for paid or real-student traffic.** Score moved 78 → 82 only because restore, 1000 RQ jobs, and Redis/Postgres chaos produced artifacts. It does not move to 98 without secret manager, image scan, staging HA, 50k-user SLO pass, and host paging.
