# Alert Validation Report — AcademicCheck AI

Date: 2026-09-07  
Lifecycle audit. Catalog YAML and Grafana JSON do **not** mean alerts are in production.

## Required stages

| Stage | Required proof | Result | Evidence |
| --- | --- | --- | --- |
| **Trigger** | Series exists and rule would fire | **Partial** — some series exist; rules not loaded | `/api/metrics/prometheus`; `ops/prometheus/alert-rules.yml` unused |
| **Escalation** | Unacked → backup / IC | **Fail** | Vacant on-call (OPS-01). No policy object |
| **Acknowledgement** | Human ack in pager/ITSM | **Fail** | No PagerDuty/Alertmanager |
| **Resolution** | Auto-resolve when signal clears | **Fail** | Redis recover still 503 at +3 s; no resolve event |
| **Closure** | Ticket closed + postmortem | **Fail** | No production paging tickets |

Go-live Grafana/PagerDuty: **FAIL**. Observability **70 / 98**. Operations **58 / 98**. On-call readiness: **not certified**.

## Per-alert

| ID | Trigger | Escalation | Ack | Resolution |
| --- | --- | --- | --- | --- |
| A-READY | Local ready 503 | Fail | Fail | Fail |
| A-5XX | Series exists; page **not run** | Fail | Fail | Fail |
| A-LAT | Process p95; live_100 **fail 1129 ms** with **no page** | Fail | Fail | Fail |
| A-CPU | **Not emitted** | — | — | — |
| A-MEM | **Not emitted** | — | — | — |
| A-DISK | **Not emitted** | — | — | — |
| A-DB | Chaos ready 503 (2026-09-07T12:36:39Z) | Fail | Fail | Local recover 200, not paged |
| A-DBSAT | **Not emitted** | — | — | — |
| A-REDIS | Local POST 1 (`cert_alert_fire.json`) | Fail | Fail | Fail (+3s still 503) |
| A-WORKER | Series exists; kill drill **no page** | Fail | Fail | 1 stuck job (cert) |
| A-QUEUE | Depth only; page not run | Fail | Fail | Fail |
| A-STORAGE | **Not emitted** | — | — | — |
| A-PAY | Incomplete metric; keys absent | Fail | Fail | Fail |
| A-WH | Series exists; page not run | Fail | Fail | Fail |
| A-AI | Pytest circuit only | Fail | Fail | Fail |
| A-AUTH | Logs only | Fail | Fail | Fail |
| A-CERT | **Not emitted** | — | — | — |
| A-BACKUP | **Not emitted** | — | — | — |
| A-NET | **Not emitted** | — | — | — |

## Residual

OPS-06, OPS-12, OPS-13, OPS-23, OPS-26. Close those before claiming alerting excellence.
