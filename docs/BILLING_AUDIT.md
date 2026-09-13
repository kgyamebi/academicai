# Billing audit and financial integrity

Date: 2026-09-09  
Live charges: **false** (`ops/cert_payment_keys.json`)

Ledger pytest remains the only financial proof. Live Stripe / Paystack / Flutterwave: **FAIL**.

## Proven in automated tests

- Checkout without provider keys returns 503 (no fake paid state)
- Guests cannot checkout
- Webhook replay does not double-grant
- Failed-then-success still grants; success-then-late-failure does not revoke
- Full refund claws credits once
- Partial refund claws credits proportionally
- Cancelled charge does not grant a plan
- Second successful subscription cancels the previous active subscription
- Expired credits read as zero
- Unsigned Paystack / Flutterwave webhooks return 400
- Illegal subscription transitions return 409 (`subscription_fsm`)
- Stale Paystack/FLW events with `paid_at` older than tolerance return 400
- Silent wallet corruption blocks further grants (409)

This session: sandbox/critical/reconcile **56 passed**; integrity FSM + related **11 passed**.

## Not proven (live certification still open)

Live $1 / ₵1 / ₦100 charges, provider-side refunds, and out-of-order events from the actual Stripe, Paystack, and Flutterwave dashboards were **not** executed. Those remain a launch P0.

Do not treat this file as a live Payment Reliability Certificate.
