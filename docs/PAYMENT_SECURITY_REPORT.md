# Payment Security Report — AcademicCheck AI

Date: 2026-09-09  
Evidence: `test_billing_critical.py`, `test_billing_sandbox_scenarios.py`, reconcile alert tests.

| Control | Stripe | Paystack | Flutterwave |
| --- | --- | --- | --- |
| Webhook signature | Yes | Yes | Yes |
| Replay protection | Yes | Yes | Yes |
| Server-side amounts | Yes | Yes | Yes |
| Unmatched actionable → 503 | Yes | Yes | Yes |
| Cancel IDOR | 404 | — | — |

Live provider certification: **FAIL** (HAL-01–03). Sandbox: **PASS**.
