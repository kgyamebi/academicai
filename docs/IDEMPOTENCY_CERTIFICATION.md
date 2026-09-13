# Idempotency Certification — AcademicCheck AI

Date: 2026-09-09  

| Surface | Key / mechanism | Proven? |
| --- | --- | --- |
| Checkout create | `Payment.idempotency_key` unique | PASS sandbox |
| Stripe Session | API idempotency_key | Code |
| Webhook delivery | `WebhookEvent.event_id` | PASS |
| Payment apply | `provider_event_id` unique + row lock | PASS |
| Browser retry | Same monthly/hourly key | PASS S1 |
| Provider retry | Duplicate event short-circuit | PASS S2/S4 |
| Crash mid-apply | Nested IntegrityError / FOR UPDATE | PASS concurrent |

**Certification: PASS (repository/sandbox).** **FAIL (live).**
