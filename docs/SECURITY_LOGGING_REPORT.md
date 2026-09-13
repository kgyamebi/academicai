# Security Logging Report — AcademicCheck AI

Date: 2026-09-07  
Logger: structlog; production JSON; redaction of token/password/secret keys (`logging.py`).

| Event class | Logged? | Store | Test |
| --- | --- | --- | --- |
| Login success/fail/lockout | Yes | `security_events` | lockout test |
| Refresh reuse | Yes | security_events critical | refresh reuse test |
| Authorization miss | HTTP 404 generic | request_id in logs | isolation |
| Admin actions | `AdminAuditLog` on admin routes | table | code |
| Permission / role | role on user; no dedicated “role change” API in this product | — | n/a |
| Billing | webhook unmatched metric; payment rows | counters + DB | billing tests |
| Webhooks | event_id table | DB | idempotency |
| Citation verify | `citation_verify` security event | security_events | citations test |
| Suspicious upload | 400 body, no stack | — | document_security |

Assignment text must not appear in incident channels (IR plan).

**PARTIAL.** Logs exist. They are not a SIEM (SEC-09, SEC-14).
