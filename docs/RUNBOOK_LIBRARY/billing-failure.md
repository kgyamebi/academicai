# Runbook: Billing failure (umbrella)

**SEV:** 1 if ledger/PSP disagree; 2 if all checkouts 503.  
**Owner:** Payments (unassigned).  
**Provider runbooks:** `stripe-failure.md`, `paystack-failure.md`, `flutterwave-failure.md`, `payment-webhook-failure.md`.  
**Evidence:** `ops/cert_payment_keys.json` — live certification **blocked**.

## Detection

Checkout 503/502; circuit open; unmatched webhooks; user “paid but no plan.”

## Impact

Revenue path down or money wrong (SEV-0 if at scale).

## Mitigation

Stop paid traffic if disagree. Never `UPDATE credits` or plan slugs in SQL.

## Recovery

Follow the **specific PSP** runbook. Refunds: provider dashboard + `apply_refund` only.

## Escalation

SEV-1 finance + IC. Legal retention of payment rows on account delete. OPS-11 (PSP sub not cancelled).

## Validation

Payment statuses match PSP events. Idempotent `event_id`.

## Postmortem

SEV ≥ 2 always; SEV-1 if mismatch.
