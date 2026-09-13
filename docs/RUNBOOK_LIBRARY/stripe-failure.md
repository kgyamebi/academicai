# Runbook: Stripe failure

**SEV:** 1 if charges or grants may be wrong; 2 if checkout 503.  
**Owner:** Payments (unassigned).  
**Evidence:** `ops/cert_payment_keys.json` Stripe `secret_present: false`. Checkout 503 is **expected** without keys (`_stripe_checkout`). Live charges **not executed**.

## Detection

- Checkout 503 `"Stripe is not configured."` or 502 `"Could not start Stripe checkout."`
- Circuit `stripe` open
- Dashboard Stripe (not available here)
- Webhook path: `payment-webhook-failure.md`

## Impact

USD card checkout down. Other PSPs may still work **if their keys exist** (they do not in this cert). Ledger must not be hand-edited.

## Mitigation

1. Stop sending users to Stripe if ledger/PSP disagree.
2. Never `UPDATE credits` in SQL.
3. Circuit open = fail-closed (`allow("stripe")`).

## Recovery

1. Confirm `STRIPE_SECRET_KEY` / webhook secret in the **manager** (not git).
2. Stripe Dashboard: payments vs `payments` table `provider=stripe`.
3. Replay webhook with valid HMAC only. Idempotent `event_id`.
4. Refunds: Stripe Dashboard + existing `apply_refund` path.

## Escalation

SEV-1 money + IC. Account-delete does **not** cancel Stripe subs (OPS-11).

## Validation

Staging checkout with **test** keys (not proven here). `billing.successful_payments` is process-local — not a ledger.

## Postmortem

SEV ≥ 2 always; SEV-1 if any mismatch. Attach Stripe event ids, not PAN.
