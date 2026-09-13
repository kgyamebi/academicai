# Incident Response Plan — AcademicCheck AI

Date: 2026-09-09  
On-call names: **unassigned**. PagerDuty: **payload supported; hosted routing unproven**. This document is operable as procedure; it is **not** a staffed IR function.

Related: `docs/INCIDENT_COMMAND_GUIDE.md`, `docs/POSTMORTEM_PROCESS.md`, `docs/ONCALL_OPERATIONS_GUIDE.md`, `docs/SERVICE_CATALOG.md`, `docs/RUNBOOK_LIBRARY/README.md`.

## Severity framework

| Sev | Name | Examples | Ack target (design) | Update cadence | Recovery expectation | Comms |
| --- | --- | --- | --- | --- | --- | --- |
| **SEV-0** | Catastrophic | Active tenant data exfil; confirmed double-charge **at scale**; total irreversible data loss; legal-mandated halt | 5 min | 15 min | Stop **all** paid traffic; preserve evidence; IC + legal; no “we think it’s fine” | Customers + legal as required; status issue immediately |
| **SEV-1** | Critical | Isolated leak under investigation; single-tenant money wrong; restore in progress; mass session revoke | 15 min | 30 min | Stop paid traffic if ledger/PSP disagree; fail closed | Customers if data/money confirmed; else internal + pending public |
| **SEV-2** | Major | `/api/ready` 503; workers 0; a PSP checkout down; p95 collapse (see HTTP cert fail at 100 in-flight) | 30 min | 30 min | Fail closed; restart/scale; no fake success | Internal ≤ 15 min of detect; public if user-visible > 30 min |
| **SEV-3** | Degraded | Single-tenant defect; AI circuit open; elevated 4xx; one region of email | Next business hours if no page | Daily if multi-day | Ticket; no prod schema change without backup | Internal only |
| **SEV-4** | Minor | Docs, CI flake, non-prod, runbook typo | Business hours | None | Normal change process | None |

Escalate **up** if: money involved, tenant isolation in doubt, restore started, or impact spreads. Escalate **down** only when impact is measured, not hoped.

SEV-0 vs SEV-1: use 0 when harm is **ongoing or irreversible**. Use 1 when critical but containable.

## Escalation path

1. Detecting engineer (ready probe, user report, or log).
2. On-call engineer — **vacant**.
3. Service owner from catalog — **vacant**.
4. Incident commander — **vacant**.
5. External: PSP support, cloud DB support, legal (SEV-0/1).

If a seat is vacant, the detecting engineer **is** IC until a human is named. That is a residual Critical risk, not a workaround to celebrate.

## Communication flow

```
Detect → Classify SEV → Open `.github/ISSUE_TEMPLATE/incident.md`
      → Bridge (not provisioned)
      → Timestamped updates on the issue
      → SEV-0/1/2 stakeholders (names vacant)
      → Mitigate using RUNBOOK_LIBRARY
      → Resolve → postmortem process
```

Do not paste assignment text, tokens, or card data into incident channels.

## Stakeholder notification

| Audience | When |
| --- | --- |
| Engineering | SEV-0/1/2 immediately |
| Payments owner | Any billing/webhook SEV-0/1/2 |
| Security owner | Leak, auth, IDOR |
| Legal | SEV-0; any confirmed PII/tenant leak |
| Users | Confirmed data/money impact, or SEV-0/1/2 user-visible > 30 min |
| Status page | **Not provisioned** — the incident issue is the record |

## Status update procedure

Every cadence tick while SEV-0/1/2 is open, post:

1. Current SEV and user impact (one sentence)
2. What we know / what we are doing
3. Next check time
4. `X-Request-ID` / `job_id` samples (not PII)

## First 15 minutes (SEV-0/1/2)

1. `GET /api/live` and `GET /api/ready`
2. Bind logs by `request_id` (HTTP). Workers: `job_id` (OPS-25).
3. No one-off production SQL without a backup.
4. Billing: never grant credits in SQL.
5. Open the matching runbook.

## Residual

This plan cannot page a human until OPS-01 and OPS-06 close. Design ack targets are therefore **unmet by construction**.
