# Runbook: Data corruption

**SEV:** 0 if irrecoverable tenant/payment data; 1 if restore in progress.  
**Owner:** Data (unassigned). **Alert:** none — no checksum exporter. Detected by counts, user reports, or failed restore validate.

## Detection

- `ops/validate_restore.py` count mismatch
- Payments/credits disagree with PSP
- ORM errors / constraint violations after a deploy
- Silent wrong reports (integrity — treat as SEV-1 until scoped)

## Impact

Wrong academic feedback is a product-integrity incident; wrong money is SEV-0/1. Isolation break is SEV-0.

## Mitigation

1. Stop writes if corruption is spreading (maintenance / ready fail).
2. **Never** “fix” credits, scores, or tenant FKs with ad-hoc SQL.
3. Preserve the broken volume (snapshot) before restore.

## Recovery

1. Snapshot / dump the current (bad) state for forensics.
2. Restore last known-good dump to **scratch**; validate.
3. Cut over only after counts match expected dump.
4. PITR to a time before corruption: **not proven** (OPS-03).
5. If only one tenant: still no SQL surgery without a written IC decision and backup.

## Escalation

SEV-0/1 IC + data + (payments if ledger) + (security if isolation).

## Validation

`ops/validate_restore.py`. Spot-check payment rows vs PSP (keys may be absent → cannot validate live).

## Postmortem

Mandatory. Attach counts. Do not include assignment text.
