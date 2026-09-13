# Runbook: Security incident

**SEV:** 0 active exfil / confirmed cross-tenant read; 1 leak under investigation or mass session theft; 2 isolated IDOR blocked.  
**Owner:** Security (unassigned).  
**Also:** `docs/SECURITY_RUNBOOK.md`, `docs/THREAT_MODEL.md`.

## Detection

- `security_events` (refresh_reuse, citation_verify, etc.)
- User report; anomalous 4xx
- Isolation pytest is **repo-only**, not detection in production

## Impact

Student/lecturer data exposure; legal. Billing freeze if ledger unknown.

## Mitigation

1. Contain: rotate JWT (`ops/rotate-secrets.md`), revoke families, disable compromised admin.
2. Preserve logs and `security_events`. Do not wipe.
3. Stop paid traffic if needed.
4. Do not announce “no data lost” without restore + access-log review.

## Recovery

Follow IR plan SEV-0/1. Independent pentest is still **FAIL** — commission one after a live leak; do not treat repo tests as that pentest.

## Escalation

SEV-0/1: IC, legal, users if required by law. Postmortem in 3–5 business days.

## Validation

Isolation still holds in staging. Refresh reuse recorded.

## Postmortem

Mandatory SEV ≥ 1. No assignment text. Template + `docs/POSTMORTEM_PROCESS.md`.
