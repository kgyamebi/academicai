# Reliability Monitoring Report — AcademicCheck AI

Date: 2026-09-07  
Observability **70 / 98**. Grafana/Prometheus/Alertmanager/PagerDuty **not running**. OTel **not installed**.

## Implemented in-app

| Signal | Where | Gap |
| --- | --- | --- |
| Structured logs | structlog JSON in prod | Worker HTTP `request_id` unbound |
| Correlation | `X-Request-ID` | No distributed traces |
| Metrics | `/api/metrics/prometheus` process-local | Lost on restart |
| Queue / workers | gauges | Age not emitted |
| Circuits | `academiccheck_circuit` | Process-local |
| Billing unmatched | counter | No fail counter |
| Dashboards | `ops/grafana/*.json` import specs | **Not deployed** |
| Alert rules | `ops/prometheus/alert-rules.yml` | **Not loaded** |

## Requested alerts

| Alert | Can fire from app scrape? | Delivery proven? |
| --- | --- | --- |
| Queue backlog | Depth only | No pager |
| Worker crash | workers=0 (if scraped) | No |
| Database outage | `academiccheck_database` | Local Redis sink once; PG chaos no page |
| Storage outage | **No series** | No |
| API errors | `http.5xx` | No |
| High latency | process p95 | No |
| Failed restores | **No series** | No |
| Failed backups | **No series** | No |

Alert fatigue: no production pages exist — fatigue is **not applicable**. Local sink fired **1** event.

## Verdict

**FAIL** reliability monitoring as an operated system. **PASS** scrape surface + structlog on HTTP.
