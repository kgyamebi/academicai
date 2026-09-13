# Runbook: Paystack failure

**SEV:** 1 if charges or grants may be wrong; 2 if checkout 503.  
**Owner:** Payments (unassigned).  
**Evidence:** Paystack secrets **false** in `ops/cert_payment_keys.json`. Pytest HMAC exists; live certification **blocked**.

## Detection

- Checkout 503/502 on `provider=paystack`
- Circuit `paystack` open
- Header `x-paystack-signature` rejects (400) vs apply miss

## Impact

Paystack checkout down. Same ledger rules as Stripe. Do not mix providers on one `payment_id`.

## Mitigation

Fail closed. No SQL credit grants. Do not disable signature checks.

## Recovery

1. Keys: `PAYSTACK_SECRET_KEY` / webhook secret (or secret key used as HMAC material in code).
2. Paystack Dashboard vs local `payments` rows.
3. Replay webhook; `record_webhook_event` idempotency.
4. OPS-11: account delete does not cancel Paystack subscriptions.

## Escalation

SEV-1 money + IC.

## Validation

Signature round-trip is pytest-only until staging keys exist.

## Postmortem

Required for SEV ≥ 2. No card data in the write-up.
