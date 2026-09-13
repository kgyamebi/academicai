# Payment Recovery Certification — AcademicCheck AI

Date: 2026-09-09  

## What is protected in Postgres

Payments, payment_transactions, credits, credit_transactions, subscriptions — restored with DB dump (`cert_restore_audit` counts for payments/credits/subscriptions = 1 seed row each).

## Automation

| Tool | Purpose | Proven? |
| --- | --- | --- |
| `ops/reconcile_billing.py` → `run_billing_reconcile.py` | Snapshot vs ledger; `--alert` on mismatch | pytest `test_billing_reconcile_alert.py` |
| Webhook HMAC + replay table | Lost/duplicate/OOO | Sandbox suite PASS (`docs/BILLING_SANDBOX_VERIFICATION.md`) |
| Live PSP event replay | Provider dashboard | **AWAITING HUMAN** (HAL-01–03) |

## Scenarios

| Scenario | Sandbox | Live |
| --- | --- | --- |
| Lost webhook | Covered (idempotent grant path) | UNPROVEN |
| Duplicate webhook | PASS | UNPROVEN |
| Out-of-order refund | PASS (503 defer) | UNPROVEN |
| Provider failure | Circuit / 503 code | Chaos `billing_provider_kill` **not_run** |
| Ledger after DB restore | Rows restore with dump | Money truth still PSP |

## Verdict

**PASS** sandbox payment recovery logic + reconcile alert path.  
**FAIL** live payment recovery certification. Do not treat dump restore as proof of no double-charge in production.
