# Billing Risk Register — AcademicCheck AI

Date: 2026-09-09  
Rule: live PSP unproven = open Critical. Sandbox pytest PASS does not close live risk.

| ID | Severity | Risk | Evidence / treatment |
| --- | --- | --- | --- |
| BILL-R01 | Critical | Live double-charge / miss-grant unproven | HAL-01–03; harness awaiting human |
| BILL-R02 | Critical | Provider cancel on account delete missing | HAL-04 |
| BILL-R03 | High | Wallet dual-write drift via raw SQL | Detected by `wallet_matches_ledger`; **grant now fail-closed** |
| BILL-R04 | High | Paystack/FLW without Stripe-style signed timestamp | Freshness check when `paid_at`/`created_at` present; missing ts → metric only |
| BILL-R05 | High | No live API reconcile (snapshot file only) | `billing_reconcile` CLI |
| BILL-R06 | Medium | User cancel leaves `active` + `cancel_at_period_end` | Documented; period-end job not separate |
| BILL-R07 | Medium | Formal FSM newly enforced; historical free strings | `subscription_fsm.py` |
| BILL-R08 | Medium | Concurrent multi-tab checkout weakly keyed | Monthly/hourly idempotency buckets |
| BILL-R09 | Medium | Circuit breaker in-process | Lost on restart |
| BILL-R10 | Low | Display FX rates static | Not settlement amounts |
| BILL-R11 | Low | Credit txn status mutated (reserve→consume) | Not append-only; amounts immutable |

## Corruption / duplicate / race paths (treated)

| Path | Status |
| --- | --- |
| Duplicate webhook | Idempotent WebhookEvent + PaymentTransaction (**PASS** sandbox) |
| Concurrent same event | IntegrityError handled (**PASS** S4) |
| OOO refund before success | 503 defer (**PASS**) |
| Orphan successful without txn | Reconcile `missing_success_txn` |
| Subscription illegal transition | FSM 409 (**PASS** unit) |
