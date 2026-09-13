# Reliability Observability Report — AcademicCheck AI

Date: 2026-09-09  

| Signal | Present | Operated? |
| --- | --- | --- |
| Structured logs | Yes | Hygiene CI |
| Counters / gauges / p95 | Yes | `/api/metrics` |
| Prometheus text | Yes | Hosted scrape HAL-10 open |
| Tracing module | OTEL optional | Hosted open |
| live / ready / health | Yes | Chaos proven ready 503 |
| Alerts: 5xx, worker, payment, backup, unhandled | `alerting.py` | Webhook/file proven; PagerDuty payload; hosted PD open |
| Queue depth / workers | Ready + gauges | |
| Circuit gauges | Prometheus | pytest |

**PASS** in-process observability. **FAIL** hosted reliability monitoring (Grafana/Alertmanager/on-call).
