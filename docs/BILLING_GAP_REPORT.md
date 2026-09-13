# Billing Gap Report — AcademicCheck AI

Date: 2026-09-07  
Billing score remains **93 / 99**. **Sandbox-verified; pending live-transaction confirmation of account config before public launch.** Evidence: `docs/BILLING_SANDBOX_VERIFICATION.md`, `ops/cert_billing_sandbox_pytest.txt` (53 passed). `ops/cert_payment_keys.json`: all secrets absent.

| Requirement | Code | Pytest | Live | Classification |
| --- | --- | --- | --- | --- |
| Stripe adapter + webhook | Yes | Yes | No | PARTIAL |
| Paystack | Yes | Yes | No | PARTIAL |
| Flutterwave | Yes | Yes | No | PARTIAL |
| Subscriptions | Yes | Ledger tests | No provider portal | PARTIAL |
| Credits | Yes | reserve/consume/refund | No live pack purchase | PARTIAL |
| Refunds | Ledger states | Yes | No live refund | PARTIAL |
| Webhooks HMAC + replay | Yes | Yes | No | PARTIAL |
| Idempotency | event_id unique | Yes | No | PARTIAL |
| Financial ledger | Payments + credit_transactions | Yes | n=1 on restore DB | PARTIAL |
| Frontend cannot mark paid | Yes | Yes | — | PASS |
| Account delete cancels local sub | **This pass** | Yes | Provider cancel missing | PARTIAL |
| Card data stored | No | — | — | PASS |

**Billing corruption paths in pytest:** replay/out-of-order covered. **Live double-grant:** unproven. **Do not take paid traffic.**
