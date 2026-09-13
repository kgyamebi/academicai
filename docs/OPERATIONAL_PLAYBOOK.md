# Operational Playbook — AcademicCheck AI

Date: 2026-09-07  
Detailed runbooks already exist: `docs/DEPLOYMENT_RUNBOOK.md`, `docs/MONITORING_RUNBOOK.md`, `docs/RECOVERY_RUNBOOK.md`, `docs/BILLING_RUNBOOK.md`, `docs/SECURITY_RUNBOOK.md`, `docs/INCIDENT_RESPONSE_PLAN.md`. This page is the engineering-quality index.

## Health

| Endpoint | Meaning |
| --- | --- |
| `GET /api/live` | Process up |
| `GET /api/ready` | DB (+ Redis when configured); **503** if not |
| `GET /api/metrics` | JSON counters, circuits, latency snapshot |
| `GET /api/metrics/prometheus` | Scrape text |

Chaos (local): Redis/PG down → live 200, ready 503, recover 200 (`ops/cert_chaos_results.json`).

## Queue

- Depth: `academiccheck_queue_depth` or metrics JSON.
- DLQ queue name: `analysis_dlq`.
- Stale jobs: `reap_stale_jobs` (indexes in Alembic 007).
- Worker death drill: **1 queued stuck** — do not claim zero-stuck recovery (`ops/cert_worker_death.json`).

## Restore

Local Docker RTO 21.317 s (`ops/cert_restore_audit.json`). Managed PITR: **false**. Encrypted backups: **not** in this environment.

## Billing

Do not take paid traffic. `ops/cert_payment_keys.json`: all secrets absent, `live_certification: blocked_no_provider_keys`.

## Deploy / rollback

- CI does not deploy.
- Local blue-green proxy only (`ops/cert_bluegreen_results.json`).
- Production secrets: manager, not git.

## Incidents

Follow `docs/INCIDENT_RESPONSE_PLAN.md`. Correlate with `X-Request-ID`.

## What is not operational yet

Grafana, Prometheus server, PagerDuty, 99.95% uptime window, staging HA, image scanning.
