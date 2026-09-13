# Financial Integrity Report

Date: 2026-09-07  
Live charges: **false** (`ops/cert_payment_keys.json`)

## Automated ledger (pytest `tests/test_billing_critical.py`)

28 tests passed in this session including queue/injection files together: **28 passed** (`test_billing_critical` + `test_queue_recovery` + `test_reliability_injection`).

Proven in-repo (not live PSP):

- Checkout without keys fails closed
- Guest cannot checkout
- Webhook replay does not double-grant
- Failed-then-success grants; success-then-late-failure does not revoke
- Full and partial refund clawback
- Cancelled charge does not grant
- Second subscription cancels the first
- Expired credits unusable
- Paystack/Flutterwave bad signature rejected; Paystack valid signature roundtrip (test secret)

## Live PSP

Stripe / Paystack / Flutterwave secrets: **all absent**. No $1 / ₵1 / ₦100 charge, refund, or dashboard event was executed.

## Verdict

**FAIL** live payment certification. Ledger unit tests are not a PSP certificate.
