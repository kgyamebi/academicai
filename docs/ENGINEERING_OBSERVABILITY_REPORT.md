# Observability Report — AcademicCheck AI

Date: 2026-09-07  
Score: **70 / 100**. Gate 98. **Fail.**  
Do not treat the panel specs below as deployed Grafana.

## Implemented and verified in-repo

| Signal | Where | Verified |
| --- | --- | --- |
| Structured logs | structlog + `request_id` | `X-Request-ID` tests |
| Process metrics JSON | `GET /api/metrics` | pytest |
| Prometheus text | `GET /api/metrics/prometheus` | pytest (prior) |
| Health | `/api/live`, `/api/ready` | chaos JSON |
| Circuits | `ai_circuits` on metrics | code |
| Local alert sink | HTTP POST on ready 503 | `ops/cert_alert_fire.json` |

Not installed here: OpenTelemetry SDK, Prometheus server, Grafana, Alertmanager, PagerDuty. Import-only dashboard JSON lives in `ops/grafana/` and is **not running**. Sentry initializes only if `SENTRY_DSN` is set (unset in this environment).

Metrics are **process-local** (`app/core/metrics.py`). Scraping every replica is required. Restart zeros counters.

## Failure classes (code counters / logs, not a hosted dashboard)

| Class | Code hook |
| --- | --- |
| API failures | `http.4xx` / `http.5xx`, `unhandled_error` |
| Queue failures | `queue_unavailable`, DLQ `analysis_job_dead_letter`, `poison_analysis_job` |
| Database failures | ready 503; `statement_timeout` / `lock_timeout` |
| Upload failures | documents 400 paths |
| Billing failures | 502/503 provider paths; webhook 400 |
| Analysis failures | `fail_job`, job `error` column |

## Dashboard specifications (NOT DEPLOYED)

These queries assume a Prometheus that scrapes `/api/metrics/prometheus` on each replica. No scrape config was applied on a host in this pass.

### Operations

- `academiccheck_ready`
- `academiccheck_http_latency_ms{quantile="0.95"}`
- `rate(academiccheck_http_5xx[5m])`
- `academiccheck_queue_depth`
- `academiccheck_workers`

### Infrastructure

- `academiccheck_database`
- `academiccheck_redis`
- Host CPU/memory: **not emitted by the app** (need node exporter — absent)

### Billing

- App does not export `billing_webhook_ok` as a first-class Prometheus name unless present in process counters after traffic.
- Use structured logs + PSP dashboards. Live PSP: **no keys**.

### Analysis

- `academiccheck_queue_depth`, `academiccheck_workers`
- `academiccheck_circuit` (AI/S3/billing/SMTP circuits)

### Security

- Rely on `security_events` table + application logs (`refresh_reuse`). No SIEM shipped.

Alert names: `docs/ALERT_CATALOG.md`. Validation of fire: local sink only.

## Verdict

Observability is request-id + process scrape + local 503 alert. **Not** production-certified. Grafana/OTel remain empty.
