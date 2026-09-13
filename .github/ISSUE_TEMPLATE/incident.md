---
name: Incident
about: Open a SEV-1–4 incident (use this instead of chat-only notes)
title: "[SEV-?] short user impact"
labels: []
---

## Severity

- [ ] SEV-0 Catastrophic (active exfil, double-charge at scale, irreversible loss)
- [ ] SEV-1 Critical (data leak, money wrong, restore in progress)
- [ ] SEV-2 Major (ready 503, workers 0, checkout down, p95 collapse)
- [ ] SEV-3 Degraded (single-tenant, AI circuit, elevated 4xx)
- [ ] SEV-4 Minor (docs, CI, non-prod)

See `docs/INCIDENT_RESPONSE_PLAN.md`.

## Impact

- What users see (no assignment text):
- Paid traffic affected? yes / no / unknown
- Started (UTC):
- Detected (UTC):

## Signals

- `/api/live`:
- `/api/ready`:
- `X-Request-ID` samples:
- Alert IDs (`docs/ALERT_CATALOG.md`):

## Services

From `docs/SERVICE_CATALOG.md` (owners are unassigned until named):

## Runbooks followed

`docs/RUNBOOK_LIBRARY/`

## Status updates (every 30 min for SEV-1/2)

| UTC | SEV | Known | Next check |
| --- | --- | --- | --- |

## Commander

IC (vacant until named):  
Detecting engineer:
