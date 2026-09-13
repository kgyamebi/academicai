# Runbook: Restore failure

**SEV:** 1 while restore is the recovery path; 0 if primary is gone and restore fails.  
**Owner:** Data (unassigned).  
**Evidence:** Local RTO ~21.3 s (`ops/cert_restore_audit.json`). `managed_postgres: false`.

## Detection

- `pg_restore`/`psql` errors
- `validate_restore.py` mismatch
- Scratch DB missing relations

## Impact

Cannot recover. Do not overwrite primary with a partial restore.

## Mitigation

Keep primary if it still serves. Work only on `academiccheck_restore` (or equivalent scratch).

## Recovery

1. Re-run restore into a **new** scratch database.
2. Fix dump corruption by using an older dump (if any).
3. Do not `alembic downgrade` to “undo” a failed restore.
4. Objects/files are **not** in `pg_dump` — storage restore separate and unrun.

## Escalation

SEV-0/1 IC + data.

## Validation

Counts match the dump used. API pointed at scratch only after IC approval.

## Postmortem

Mandatory. Attach validate output, not table contents.
