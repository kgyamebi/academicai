# Fraud Protection Report — AcademicCheck AI

Date: 2026-09-09  

| Abuse | Control |
| --- | --- |
| Webhook forgery | Signature + alert |
| Replay | WebhookEvent + txn unique |
| Duplicate purchase | Idempotency keys |
| Credit farming via webhook | No double grant |
| Payment amount tampering | Server-side plan/pack prices |
| Subscription abuse (stack) | Prior active cancelled on new paid |
| Stale webhook | Skew check when ts present |

**PASS** controls in sandbox. **FAIL** live fraud red-team.
