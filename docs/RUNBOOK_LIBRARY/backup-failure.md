# Runbook: Backup failure

**SEV:** 1 if last successful backup older than policy (target nightly; **not enforced**).  
**Owner:** Data (unassigned). **Alert:** A-BACKUP **not emitted** (OPS-26).

## Detection

- Missing/empty gzip under `BACKUP_DIR`
- Restore validate fail
- Disk full (A-DISK not emitted — check the host manually)

## Impact

RPO slips to “unknown.” Paid traffic should not start without a verified copy.

## Mitigation

Do not delete the last known-good dump to free disk. Do not assume WAL/PITR (unproven).

## Recovery

1. `ops/backup_postgres.sh` — confirm non-empty `academiccheck-*.sql.gz`.
2. Restore to scratch + `ops/validate_restore.py`.
3. Offsite/encrypted copies: **not proven**.
4. Provider snapshots: `ops/PITR.md` unverified.

## Escalation

SEV-1 until a verified copy exists.

## Validation

`ls -lh`; scratch restore counts.

## Postmortem

SEV-1. Include dump timestamps. No tenant row dumps in the write-up.
