# Billing audit and financial integrity

Date: 2026-09-06

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

## Not proven (live certification still open)

Live $1 / ₵1 / ₦100 charges, provider-side refunds, and out-of-order events from the actual Stripe, Paystack, and Flutterwave dashboards were **not** executed in this engagement. Those remain a launch P0.

Do not treat this file as a Payment Reliability Certificate.
