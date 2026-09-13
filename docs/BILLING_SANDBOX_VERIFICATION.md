# Billing Sandbox Verification — AcademicCheck AI

Date: 2026-09-07  
Mode: **Sandbox / test-mode logic only** (no live keys present in this environment).  
Evidence run: `ops/cert_billing_sandbox_pytest.txt` — **53 passed** (`test_billing_sandbox_scenarios.py` + `test_billing_critical.py`).  
Key artifact: `ops/cert_payment_keys.json` — `any_provider_key: false`, `live_charges_executed: false`.

## Explicit certification boundary

This document proves **application logic** under simulated Stripe / Paystack / Flutterwave webhook and ledger conditions (sandbox-shaped payloads, HMAC signatures, DB uniqueness, row locks).

It does **not** certify:

- Live account configuration (fees, payout routing, radar/fraud rules)
- Real currency conversion / multi-currency settlement behavior
- Live payout timing or bank settlement
- Region-specific compliance (VAT, SCA challenges beyond payload shape)
- Production webhook endpoint reachability from provider IP ranges

**Sandbox-verified; pending live-transaction confirmation of account config before public launch.**

---

## Guarding logic (code)

| Guard | Location |
| --- | --- |
| Checkout idempotency key (unique) | `Payment.idempotency_key`; `_pending_payment` |
| Webhook event dedup (unique) | `WebhookEvent.event_id` + `record_webhook_event` (IntegrityError / savepoint) |
| Payment txn dedup (unique) | `PaymentTransaction.provider_event_id` + nested IntegrityError |
| Payment row lock | `SELECT … FOR UPDATE` in `apply_successful_payment` |
| Signature verify | `verify_stripe_signature` / Paystack HMAC / Flutterwave verif-hash |
| Refund-before-success defer | `apply_refund` → `False` → HTTP **503** (not marked processed) |
| Cumulative refund cap | `_refunded_amount_cents` prevents over-clawback |
| Reconciliation | `billing_reconcile.reconcile_against_provider_snapshot` |

---

## Scenario matrix

Legend: **PASS** = automated test green with evidence.  
**N/A-API** = live sandbox Dashboard/CLI charge not run (no test API keys in env); logic covered via sandbox-faithful payloads.

### 1. Idempotent charge retry

| Processor | Result | Evidence |
| --- | --- | --- |
| Stripe | PASS | `test_s1_idempotent_charge_retry_same_key[stripe]` |
| Paystack | PASS | `test_s1_idempotent_charge_retry_same_key[paystack]` |
| Flutterwave | PASS | `test_s1_idempotent_charge_retry_same_key[flutterwave]` |

Exactly one `Payment` row for the same idempotency key.

### 2. Duplicate webhook delivery

| Processor | Result | Evidence |
| --- | --- | --- |
| Stripe | PASS | `test_s2_duplicate_webhook_no_double_credit[stripe]` + `test_s2_stripe_http_duplicate_webhook` |
| Paystack | PASS | parametrized + `test_s2_paystack_http_duplicate` (HMAC with `sk_test_*` style secret in monkeypatch) |
| Flutterwave | PASS | parametrized + `test_s2_flutterwave_http_duplicate` |

One credit grant; second delivery returns `duplicate: true` or no-ops txn.

### 3. Out-of-order webhook delivery

| Processor | Result | Evidence |
| --- | --- | --- |
| Stripe | PASS | `test_s3_refund_before_success_defers_then_applies[stripe]`; HTTP 503 `test_s3_stripe_http_refund_before_success_returns_503`; fail-then-success grant |
| Paystack | PASS | same parametrized tests |
| Flutterwave | PASS | same parametrized tests |

**Bug found & fixed:** early refund previously no-op’d and could be marked processed, losing the refund after a late success. Now `apply_refund` returns `False` while pending → webhook **503** (retry). Cumulative partial refunds capped.

### 4. Concurrent webhook delivery

| Processor | Result | Evidence |
| --- | --- | --- |
| Stripe | PASS | `test_s4_concurrent_same_event_id_single_credit[stripe]`; `test_s4_concurrent_webhook_event_unique_constraint` |
| Paystack | PASS | parametrized concurrent apply |
| Flutterwave | PASS | parametrized concurrent apply |

Exactly one `PaymentTransaction` / one credit wallet outcome; unique constraint race returns False for loser.

### 5. Declined / failed charge

| Processor | Result | Evidence |
| --- | --- | --- |
| Stripe | PASS | `test_s5_failed_charge_no_credits[stripe]` |
| Paystack | PASS | parametrized + `test_s5_paystack_failed_webhook_http` |
| Flutterwave | PASS | parametrized |

No credits; payment `failed`; failure txn recorded.  
**N/A-API:** Stripe test cards `4000000000000002` etc. not charged via Dashboard (no secret key).

### 6. Partial and full refunds

| Processor | Result | Evidence |
| --- | --- | --- |
| Stripe | PASS | `test_s6_full_and_double_refund` / `test_s6_partial_then_remainder_no_over_clawback` + prior `test_billing_critical` |
| Paystack | PASS | same |
| Flutterwave | PASS | same |

Double refund (same or new event id after full) does not double-clawback; partials cannot exceed original amount.

### 7. Webhook signature verification

| Processor | Result | Evidence |
| --- | --- | --- |
| Stripe | PASS | `test_s7_stripe_forged_rejected` |
| Paystack | PASS | `test_s7_paystack_unsigned_rejected` |
| Flutterwave | PASS | `test_s7_flutterwave_bad_hash_rejected` |

Rejected with HTTP 400 before fulfillment; invalid-signature metric path covered in Pass 3.

### 8. Reconciliation check

| Processor | Result | Evidence |
| --- | --- | --- |
| Snapshot (any) | PASS | `test_s8_reconcile_flags_intentional_mismatch` — amount tamper flagged |
| Snapshot (any) | PASS | `test_s8_reconcile_clean_match` |

Job: `backend/app/services/billing_reconcile.py`. Compares internal ledger to an exported sandbox snapshot JSON (not a live List Charges API call — **no keys**).

---

## Bugs fixed this pass

1. **Out-of-order refund** — deferred with 503 until payment succeeds.  
2. **Stacked partial refunds** — capped by `_refunded_amount_cents`.  
3. **Concurrent webhook insert** — `begin_nested` + `IntegrityError` on `WebhookEvent.event_id`.  
4. **Concurrent success txn** — nested IntegrityError on `provider_event_id`.

---

## What sandbox testing CANNOT cover

1. Real multi-currency FX / rounding at the processor settlement layer  
2. Live payout / transfer timing and fee deduction  
3. 3-D Secure / SCA challenge UX and `requires_action` flows end-to-end  
4. Provider dashboard “resend” from their IP to a public HTTPS endpoint  
5. Production Radar / fraud rules and account holds  
6. Tax / VAT / invoice PDF compliance per jurisdiction  
7. Paystack/Flutterwave NGN/GHS kobo/pesewa edge cases under live keys  
8. Secret-manager–injected production webhook secrets rotation  

A small **live sandbox Dashboard drill with real test API keys** is still required before treating billing as launch-ready (Human Action List HAL-01–03).

---

## Gate note

Billing score updated to **93 / 99** with note: **Sandbox-verified; pending live-transaction confirmation of account config before public launch.** Overall remains below launch gate.
