# Security Incident Response Plan — AcademicCheck AI

Date: 2026-09-07  
Use with `docs/INCIDENT_RESPONSE_PLAN.md` (SEV-0–4), `docs/RUNBOOK_LIBRARY/security-incident.md`, `docs/SECURITY_RUNBOOK.md`.  
On-call: **unassigned**. Pager: **unwired**.

## Severity (security)

| Class | SEV | Examples |
| --- | --- | --- |
| Active exfil / confirmed cross-tenant read | 0 | IDOR returning another student’s draft |
| Credential dump / mass session theft | 0–1 | refresh_reuse storm |
| Payment ledger mismatch | 1 | double credit |
| Suspected leak under investigation | 1 | |
| Failed login spike | 3 | lockouts only |

## Credential leak

1. Identify class (JWT, PSP, AI, DB).
2. `ops/rotate-secrets.md` — dual JWT window `JWT_SECRET_PREVIOUS`.
3. Revoke refresh families if JWT.
4. Rotate PSP webhook secrets in dashboard **and** env (keys may be absent here).
5. If `.env` committed: treat Git history as compromised.
6. Postmortem 3–5 days (`docs/POSTMORTEM_PROCESS.md`).

## Breach / data exposure

1. Contain: stop paid traffic; preserve logs/`security_events`.
2. Do not announce “no data lost” without restore + access review.
3. Legal + users if required.
4. Pentest still **FAIL** in this repo — commission one after a live leak.

## Payment security incident

1. Stop checkout.
2. Never SQL-grant credits.
3. PSP dashboard vs `payments` / `webhook_events`.
4. `docs/RUNBOOK_LIBRARY/billing-failure.md` and provider runbooks.

Detecting engineer is IC if seats are vacant.
