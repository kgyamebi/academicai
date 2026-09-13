# Incident Command Guide — AcademicCheck AI

Date: 2026-09-07  
Use with `docs/INCIDENT_RESPONSE_PLAN.md`. The IC role is **vacant** until named (OPS-01).

## Roles

| Role | Duty | Who today |
| --- | --- | --- |
| Incident commander (IC) | Single decision owner; SEV; comms clock; “stop paid traffic” call | Vacant — detecting engineer acts as IC |
| Ops lead | Execute runbooks; health probes | Vacant |
| Comms | Issue updates; no assignment text | Vacant |
| Scribe | Timeline UTC | Vacant |
| Specialist | Payments / data / security as catalog | Vacant |

Do not have three people independently applying webhooks or restoring databases.

## IC checklist (SEV-0/1/2)

1. Name yourself IC in the incident issue. If you cannot stay, hand off explicitly (`docs/ONCALL_OPERATIONS_GUIDE.md`).
2. Set SEV using examples in the IR plan. When unsure between 0 and 1, start **higher**.
3. Freeze: no deploys, no `alembic`, no credit SQL, no log wipes.
4. Clock: first update within the SEV cadence even if the update is “still investigating.”
5. Pick **one** runbook. Parallel runbooks only if two failures are proven independent.
6. Health: `/api/ready` for user impact; `/api/live` only for “is the process up.”
7. Evidence: request ids, webhook `event_id`, restore counts. Screenshots of Grafana are **N/A** (not deployed).
8. Declare mitigated vs resolved: mitigated = user impact stopped; resolved = trigger gone and monitoring (such as it is) quiet.
9. Schedule postmortem before closing SEV-0/1/2 (`docs/POSTMORTEM_PROCESS.md`).

## Decision rights

| Decision | IC may | IC must not |
| --- | --- | --- |
| Stop checkout / paid traffic | Yes for SEV-0/1 money or leak | Grant credits in SQL to “make users whole” |
| Rollback image | Yes if health gate fails | `alembic downgrade` on tenant data |
| Restore | Yes to **scratch** DB first | Restore over primary without validation |
| Public statement | Draft; legal for SEV-0 leak | Claim “no data lost” without restore + access logs |

## Page / escalate (design — unwired)

| Condition | Escalate to |
| --- | --- |
| No ack in SEV ack window | Backup on-call (vacant) then IC (vacant) |
| Restore started | Data owner + IC |
| Money mismatch | Payments + IC |
| Isolation doubt | Security + IC + legal (SEV-0) |

Until a pager exists, escalation is “find a human in chat.” Record that as a contributing cause in the postmortem.
