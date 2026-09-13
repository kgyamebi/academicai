# Postmortem process — AcademicCheck AI

Date: 2026-09-07  
Template: `docs/POSTMORTEM_TEMPLATE.md`.  
Required for every **SEV-0, SEV-1, and SEV-2**. Optional for SEV-3 if user-visible > 4 hours.

This process does not create blameless culture by itself. It forbids invented metrics.

## Timing

| Step | Due |
| --- | --- |
| Incident issue marked mitigated | When user impact stops |
| Incident issue marked resolved | When trigger is gone |
| Postmortem draft | 5 business days after resolve (SEV-0: 3) |
| Review meeting | Within 10 business days |
| Action items in tracker | Same meeting; owners named (today: vacant — still write the item) |

## Rules

1. Use the template. Empty evidence fields stay empty; do not fill with “N/A, probably fine.”
2. Detection path must say **user / ready probe / log / pager**. Pager is currently unwired — say so if a human noticed first.
3. Attach `X-Request-ID`, `job_id`, webhook `event_id`, restore row counts, or `ops/cert_*.json` for drills.
4. Do not include assignment text, tokens, or PAN.
5. Action items need an owner role, due date, and the risk if skipped (map to `docs/OPERATIONS_RISK_REGISTER.md` when it is an existing OPS-ID).
6. SEV-0 leak: do not close without a pentest **plan** (pentest itself is still FAIL in this repo).
7. A drill postmortem is allowed; label it **drill**, not production.

## Review meeting

Attendees: IC, ops lead, service owner for the failed component. Today all vacant — the author of the draft still runs the review.

Output: dated notes under **Review** on the template. Follow-up SEV if a Critical action slips (treat slip as SEV-3 governance until the action is done).
