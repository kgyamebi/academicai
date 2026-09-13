# Runbook: Flutterwave failure

**SEV:** 1 if charges or grants may be wrong; 2 if checkout 503.  
**Owner:** Payments (unassigned).  
**Evidence:** Flutterwave `secret_present` / `webhook_hash_present` **false**. Live certification **blocked**.

## Detection

- Checkout 503/502 on `provider=flutterwave`
- Circuit `flutterwave` open
- `verif-hash` reject vs unmatched apply (`billing.webhook_unmatched`)

## Impact

FLW checkout down. Ledger must match FLW events. No SQL grants.

## Mitigation

Fail closed. Keep hash verification on.

## Recovery

1. `FLUTTERWAVE_SECRET_KEY` / `FLUTTERWAVE_WEBHOOK_HASH` in manager.
2. Flutterwave Dashboard vs `payments` `provider=flutterwave`.
3. Replay webhook; idempotent `event_id`.
4. OPS-11 applies (no PSP cancel on account delete).

## Escalation

SEV-1 money + IC.

## Validation

Pytest hash tests are not a live drill.

## Postmortem

SEV ≥ 2 required. Event ids only.
