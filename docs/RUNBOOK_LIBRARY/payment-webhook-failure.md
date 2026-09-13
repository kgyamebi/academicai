# Runbook: Payment webhook failure

**SEV:** 1 if apply missed/duplicated; 2 if signatures all reject (config).  
**Owner:** Payments (unassigned). **Alert:** A-WH (`academiccheck_billing_webhook_unmatched`). Unwired.

## Detection

- Counter `billing.webhook_unmatched` rising
- User paid at PSP, local `payments.status` still pending
- 400 on webhook routes (bad HMAC)

## Impact

Missed entitlements or, if someone “fixes” SQL, double grant. Duplicate `event_id` must no-op (`record_webhook_event` returns False).

## Mitigation

Do not SQL-apply. Do not turn off HMAC. Capture `X-Request-ID`, provider event id, payment id — never PAN.

## Recovery

1. Identify provider: Stripe / Paystack / Flutterwave — use that PSP runbook for keys.
2. Confirm secret matches dashboard.
3. Replay **once** from PSP dashboard.
4. If unmatched after valid HMAC: payment metadata `payment_id` missing — investigate code path, still no SQL grant.

## Escalation

SEV-1 if money/entitlement wrong. Payments + IC.

## Validation

`webhook_events` has the `event_id`. Payment row `successful` iff PSP says paid. Credits via `apply_successful_payment` only.

## Postmortem

Required for SEV ≥ 1. Attach event ids.
