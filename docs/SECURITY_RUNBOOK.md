# Security Runbook — AcademicCheck AI

Date: 2026-09-09  
Detail: `docs/RUNBOOK_LIBRARY/security-incident.md`, `docs/SECURITY_INCIDENT_RESPONSE_PLAN.md`, `docs/INCIDENT_RESPONSE_PLAN.md`.

| Incident | First actions |
| --- | --- |
| Suspected breach | Freeze paid traffic if money/data risk; rotate JWT/APP/FIELD keys; revoke sessions (`logout-all` / DB revoke); preserve logs |
| Credential leak | Rotate leaked secret via manager; invalidate sessions; force password resets if password DB risk |
| Account takeover | Lock user; revoke sessions; require password reset + MFA re-enroll for privileged |
| Payment incident | Halt checkout; reconcile vs PSP; do not SQL-grant credits |
| Webhook abuse | Rotate webhook secrets; check replay table |
| Prompt injection incident | Disable enhance/coach flag; review outputs; leave heuristic on |

Escalation: SEV table in `INCIDENT_RESPONSE_PLAN.md`. On-call roster: **vacant (HAL-11)**.
