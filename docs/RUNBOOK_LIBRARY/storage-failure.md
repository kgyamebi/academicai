# Runbook: Storage failure

**SEV:** 2 for upload/download outage; 1 if tenant files irretrievable and no object backup.  
**Owner:** Platform (unassigned). **Alert:** A-STORAGE **cannot fire** (no gauge).  
**Chaos:** `storage_kill` **not_run** (OPS-14).

## Detection

- Upload 400/5xx; download fail
- Logs `guest_purge_storage_failed`
- S3/storage circuit open if that backend is used

## Impact

New assignments cannot store bytes. Existing analysis may still read DB text if already extracted.

## Mitigation

Fail closed on upload. Do not write files into git or `/tmp` as a “hotfix” for production tenants.

## Recovery

1. Confirm disk / bucket / credentials (secrets manager **unproven**).
2. Local backend: volume mounted? Permissions?
3. Object restore from backup: **unrun**.
4. Guest expiry only runs with the job reaper (OPS-09).

## Escalation

SEV-1 if data loss. IC + data owner.

## Validation

Upload a **non-production** fixture; list/get succeeds. Never use student essays as probes.

## Postmortem

Required if any tenant file lost or SEV ≥ 2.
