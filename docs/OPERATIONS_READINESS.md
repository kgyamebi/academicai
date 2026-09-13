# Operations readiness — AcademicCheck AI

Date: 2026-09-07

## What is code/process complete

| Area | Artifact |
| --- | --- |
| Failure runbooks | `docs/RUNBOOK_LIBRARY/*` (payment/webhook, worker, backup, restore, DB, security, deploy, queue, redis, …) |
| Single-command deploy | `ops/deploy_compose.sh` (gates on `/api/live` + `/api/ready`) |
| Single-command rollback | `ops/rollback_compose.sh` (recreate + ready check) |
| Staging topology | `docker-compose.staging.yml` (`REQUIRE_QUEUE=true`, postgres, redis, api, worker) |
| Health / ready | `/api/live`, `/api/health`, `/api/ready` — used by compose healthchecks and deploy gate |
| Incident scaffolding | `docs/INCIDENT_RESPONSE_PLAN.md`, `docs/INCIDENT_COMMAND_GUIDE.md`, `.github/ISSUE_TEMPLATE/incident.md` |
| Customer-facing status | `ops/status/index.html` (polls live/ready) |
| Alert delivery (code) | Slack/Discord webhook + file sink + PagerDuty Events API v2 payload (`PAGERDUTY_ROUTING_KEY`) |

## Severity / communication (hand to on-call)

| SEV | Meaning | Initial actions |
| --- | --- | --- |
| 1 | Payments down / data loss / breach suspicion | Page primary; freeze deploys; open incident issue; status page → degraded |
| 2 | Elevated 5xx / queue stuck / ready failing | Ack alert; follow runbook; update status if user-visible |
| 3 | Partial degradation | Track; fix in business hours |

## Boundary — people-only remaining item

**This covers all process/tooling readiness.**

The one remaining item that is a people decision, not a coding task:

> **On-call staffing and rotation** — named primary/secondary, calendar, and acknowledgement SLA (HAL-11). PagerDuty account hosting is also external.

Ready to activate: set `PAGERDUTY_ROUTING_KEY` / `ALERT_WEBHOOK_URL`; assign roster in `docs/ONCALL_OPERATIONS_GUIDE.md`.
