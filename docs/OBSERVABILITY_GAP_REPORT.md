# Observability Gap Report — AcademicCheck AI

Date: 2026-09-07  
Observability score remains **70 / 98**.

| Signal | Status |
| --- | --- |
| Structured logs | PASS (structlog + request_id) |
| Metrics JSON / Prometheus text | PASS (process-local) |
| Tracing (OpenTelemetry) | FAIL — not installed |
| Dashboards (Grafana) | FAIL — not deployed (PromQL is documentation only) |
| Alerting | PARTIAL — catalog + local 503 HTTP sink; no Alertmanager/PagerDuty |
| Monitoring host | FAIL — no node exporter / managed APM here |
| Sentry | PARTIAL — init if DSN; DSN unset |

Process counters reset on restart. Replica-local. **Not production-certified.**
