# Operations dashboards — AcademicCheck AI

Date: 2026-09-07  
Observability remains **70 / 98**. These are **operating contracts**. Grafana JSON in `ops/grafana/` is **not deployed**. Prometheus/Alertmanager/PagerDuty are **not running**.

Companion (Grafana owner/purpose/alerts): `docs/OBSERVABILITY_OPERATIONS.md`.

## Signal audit (evidence)

| Signal | Status | Evidence |
| --- | --- | --- |
| Structured logging | **Pass (app)** | `structlog` JSON in production (`backend/app/core/logging.py`); secret-key redaction |
| Correlation IDs | **Pass on HTTP only** | Middleware sets/echoes `X-Request-ID`; structlog `request_id` (`backend/app/main.py`). Pytest `test_live_returns_request_id` |
| Correlation IDs on workers | **Fail / gap** | `run_analysis_job` does not bind HTTP `request_id` (OPS-25). Join via `job_id` |
| Distributed tracing | **Fail** | OpenTelemetry not installed. Sentry APM only if `SENTRY_DSN` set; default empty (OPS-23, OPS-24) |
| Metrics | **Partial** | `/api/metrics` JSON + `/api/metrics/prometheus` process-local (OPS-12) |
| Business metrics | **Partial** | `billing.successful_payments`, `citations.*` counters — not a warehouse |
| Operational health | **Partial** | `/api/live`, `/api/ready`, database/redis/workers/queue gauges |
| Host CPU/mem/disk/net | **Fail** | Not emitted (OPS-13) |

## Dashboard catalog

Every row: owner vacant until OPS-01 closes. Alert IDs from `docs/ALERT_CATALOG.md`. Grafana files are import specs.

| Dashboard | Owner | Purpose | Alert coverage | Runbooks | Grafana file |
| --- | --- | --- | --- | --- | --- |
| Infrastructure | Platform | Ready vs deps | A-READY, A-DB, A-REDIS | database, redis, high-error-rate | `ops/grafana/infrastructure.json` |
| Combined ops | Platform | Ready, p95, 5xx, queue | A-READY, A-5XX, A-LAT, A-QUEUE | high-error-rate, high-latency, queue-backlog | `ops/grafana/operations.json` |
| Database | Data | API-side ping only | A-DB. A-DBSAT **absent** | database, backup, restore, data-corruption | `ops/grafana/database.json` |
| Queues | Backend | RQ depth | A-QUEUE (no age) | queue-backlog | `ops/grafana/queues.json` |
| Workers | Backend | Registered workers | A-WORKER | worker-failure | `ops/grafana/workers.json` |
| Storage | Platform | Weak 4xx / circuit proxy | A-STORAGE **cannot fire** | storage-failure | `ops/grafana/storage.json` |
| Billing | Payments | Unmatched webhooks | A-WH; A-PAY incomplete | billing, stripe, paystack, flutterwave, webhook | `ops/grafana/billing.json` |
| AI | AI | Circuits vs heuristic | A-AI | ai-provider-failure | `ops/grafana/ai.json` |
| Security | Security | 4xx proxy; SIEM is `security_events` | A-AUTH logs only | security-incident, authentication | `ops/grafana/security.json` |
| Business | Product/ops | Process counters | none dedicated | billing-failure | `ops/grafana/business.json` |

## How to use in an incident (today)

1. `curl -sS -D- "$API/api/ready"`
2. `curl -sS "$API/api/metrics"` — counters reset on process restart.
3. Grep logs for `"request_id":"<X-Request-ID>"`.
4. Do not wait for Grafana. It is not running.
