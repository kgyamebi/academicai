# Webhook Security Report — AcademicCheck AI

Date: 2026-09-09  

| Control | Stripe | Paystack | Flutterwave |
| --- | --- | --- | --- |
| Signature / HMAC | Yes | Yes | Yes (verif-hash) |
| Timestamp / skew | Yes (`tolerance`) | Yes when `paid_at`/`created_at` present | Same |
| Missing timestamp | N/A (Stripe signed ts) | Metric + allow | Metric + allow |
| Replay / dedupe | `WebhookEvent` | Same | Same |
| Idempotent apply | `PaymentTransaction.provider_event_id` | Same | Same |
| OOO refund | 503 unprocessed | Same | Same |
| Invalid signature | 400 + metric + alert | Same | Same |

**PASS** sandbox webhook security. **FAIL** live webhook abuse drill.
