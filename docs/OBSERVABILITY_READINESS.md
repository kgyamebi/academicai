# Observability readiness — AcademicCheck AI

Date: 2026-09-07

## Code-complete

| Item | Evidence |
| --- | --- |
| Structured logging (structlog) | `backend/app/core/logging.py`; hygiene CI `tests/test_logging_hygiene.py` |
| Metrics + `/api/metrics` + `/api/metrics/prometheus` | Per-endpoint counters/p95, gauges, billing counters; `tests/test_observability_metrics.py` |
| OpenTelemetry spans | `backend/app/core/tracing.py` + middleware; console/OTLP when `OTEL_TRACES_EXPORTER` set |
| Grafana dashboards (importable JSON) | `ops/grafana/*.json` + provisioning |
| Prometheus alert rules | `ops/prometheus/alert-rules.yml` |
| Local stack to validate import/scrape | `ops/docker-compose.observability.yml` + `ops/validate_observability_stack.py` |
| Alert delivery | Webhook + file sink + PagerDuty Events API v2 in `alerting.py` |

## Ready to activate, pending external

| Item | Pending |
| --- | --- |
| Hosted Prometheus/Grafana/Alertmanager scrape | HAL-10 — provision and point at `/api/metrics/prometheus` |
| Hosted PagerDuty service + escalation policy | HAL-11 — set `PAGERDUTY_ROUTING_KEY` |
| Jaeger/OTLP collector in prod | Optional; local Jaeger in observability compose |

Run: `py -3.14 ops/validate_observability_stack.py`  
Optional: `docker compose -f ops/docker-compose.observability.yml up -d`
