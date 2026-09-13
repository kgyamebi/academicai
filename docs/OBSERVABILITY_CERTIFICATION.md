# Observability Certification Report

Date: 2026-09-07  
Score: **70 / 100** (request IDs + process metrics + local alert sink; no Grafana/PagerDuty/OTel). Gate 98. **Fail.**

## What exists

| Signal | Implementation | Validated? |
| --- | --- | --- |
| `/api/live` `/api/ready` | FastAPI | Chaos + 60 s window |
| `/api/metrics` JSON | Process counters + circuit snapshot | Pytest |
| `/api/metrics/prometheus` | Counters, queue depth, `academiccheck_circuit` | Pytest this pass |
| Request correlation | `X-Request-ID` echo + structlog `request_id` | `test_live_returns_request_id` |
| Local alert sink | HTTP POST when ready=503 | `ops/cert_alert_fire.json` |
| Grafana | Not deployed | **false** |
| Prometheus server | Not deployed | **false** |
| Alertmanager | Not deployed | **false** |
| PagerDuty | Not configured | **false** |
| Distributed traces | OpenTelemetry **not installed** | **false** |
| Sentry | Init if `SENTRY_DSN` | DSN not set here |

Metrics and circuits are **process-local**. Scraping each replica is required.

## Verdict

Observability is **not production-certified**. Request IDs are not distributed tracing.
