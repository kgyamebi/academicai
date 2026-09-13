# Payment Recovery Report — AcademicCheck AI

Date: 2026-09-07  
Providers: Stripe, Paystack, Flutterwave (`backend/app/services/billing.py`).  
Live keys: **all absent** (`ops/cert_payment_keys.json` 2026-09-07T09:47:12Z). `live_charges_executed: false`.

Chaos `billing_provider_kill`: **not_run**.

This is **not** a live payment-recovery certificate.

## Audit (code + pytest)

| Control | Where | Live-proven? |
| --- | --- | --- |
| Checkout without keys | HTTP 503 “not configured” | Expected locally; not a PSP outage |
| Provider circuit | `allow("stripe"|"paystack"|"flutterwave")` → 503 | Pytest/hardening, not live timeout |
| Webhook HMAC | per provider | Pytest (`test_billing_critical.py`, `test_reliability_failures.py`) |
| Idempotent `event_id` | `record_webhook_event` second apply False | Pytest duplicate webhook |
| Ledger apply | `apply_successful_payment` | Pytest; **not** live |
| Retry of unprocessed event | `mark_processed=False` then process | Pytest |
| Checkout idempotency key reuse after fail | `test_failed_checkout_reuses_idempotency_key` | Pytest |
| Account delete cancels PSP | Local status only (OPS-11) | **No** |

## Simulations requested

| Simulation | Result |
| --- | --- |
| Provider outage | **Not run** against Stripe/Paystack/FLW. Circuit is in-process and **lost on restart** (same as other circuits) |
| Webhook outage | **Not run**. Replay is a human PSP-dashboard action |
| Network timeout | Stripe client timeout 15s in code; **not** load-tested live |
| Retry storms | Pytest: duplicate `event_id` does not double-apply. **Not** a flood test against a real endpoint |

## Mission checks

| Check | Proven? | Evidence |
| --- | --- | --- |
| No double charges | **Pytest only** | Duplicate webhook → no second apply. Live charge **never executed** |
| No double credits | **Pytest only** | Same apply path |
| No subscription corruption | **Pytest** create/apply; live sub create/cancel **not run** | `docs/PAYMENT_CERTIFICATION.md` |
| No ledger corruption | **Pytest** + local DB restore of **1** payment row | Not a production ledger |

## Verdict

**FAIL** live recovery. **PASS** duplicate-webhook pytest on the sqlite/CI database.

Until keys exist in a secret manager and a staging PSP drill records `event_id`s, do not take paid traffic.
