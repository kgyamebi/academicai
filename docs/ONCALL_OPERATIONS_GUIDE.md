# On-call operations guide — AcademicCheck AI

Date: 2026-09-07  
**Staffed coverage today: 0 hours.** Primary and backup are unassigned (OPS-01). Alert routing to a pager is unwired (OPS-06). This guide is the intended operating model. It does **not** certify on-call readiness.

Related: `docs/INCIDENT_RESPONSE_PLAN.md`, `docs/INCIDENT_COMMAND_GUIDE.md`, `docs/ALERT_CATALOG.md`.

## Coverage expectations (design vs actual)

| Window | Design | Actual |
| --- | --- | --- |
| SEV-0/1 | 24×7 primary + backup | Unstaffed |
| SEV-2 | 24×7 primary | Unstaffed |
| SEV-3/4 | Business hours | Unstaffed |
| Follow-the-sun | Not applicable (single vacant seat) | n/a |

Do not publish “we have 24/7 on-call” until a named rotation exists.

## Response-time expectations (design — unmet)

Copied from the IR plan. Unmet until a human is paged and acks.

| SEV | Ack | Update |
| --- | --- | --- |
| 0 | 5 min | 15 min |
| 1 | 15 min | 30 min |
| 2 | 30 min | 30 min |
| 3 | next business day | daily if open |
| 4 | business hours | none |

## Escalation matrix

| From | After | To |
| --- | --- | --- |
| Firing alert (when wired) | Immediate | Primary on-call |
| Primary no ack | SEV ack window | Backup on-call |
| Backup no ack | +1× ack window | Service owner (catalog) |
| Owner no ack / SEV-0 | Immediate | IC + (legal if leak/money) |
| Vacant seats | Immediate | Detecting engineer becomes IC |

## Alert routing rules (specified, not implemented)

| Alert class | Route (design) | Actual |
| --- | --- | --- |
| A-READY, A-DB, A-REDIS, A-WORKER, A-QUEUE, A-5XX, A-LAT | Page primary | Local HTTP sink once for Redis-down |
| A-PAY, A-WH, Stripe/Paystack/FLW circuits | Page primary + payments | Unwired; keys absent |
| A-AI | Ticket / SEV-3 unless core analysis down | Unwired |
| A-AUTH | Page security if mass `refresh_reuse` | Logs only |
| A-CPU/MEM/DISK/NET, A-STORAGE, A-BACKUP, A-CERT, A-DBSAT | Page when exporters exist | **Not emitted** |

There is no Alertmanager receiver, Slack, or PagerDuty service in this repository.

## Handoff procedure

1. Open the incident issue list: any SEV-0/1/2 still open?
2. `GET /api/ready` on staging/prod when those URLs exist (`STAGING_URL` secret currently unset).
3. Queue: workers > 0, depth finite (from `/api/metrics` if the API is up).
4. Billing: no unmatched webhook spike you cannot explain.
5. Write handoff notes: SEV, next check time, runbook in use, request ids.
6. Incoming engineer acks in the issue: “on-call assumed UTC …”
7. If incoming is vacant, say so. Silent handoff to nobody is a process failure.

## Shift checklist (when staffed)

- Phone/laptop can reach the API and log store.
- Runbook library cloned / bookmarked.
- Do not test webhooks against production with replay storms.
- End of shift: handoff or explicit “nobody on-call until DATE.”
