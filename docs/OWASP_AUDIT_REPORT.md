# OWASP Top 10 Audit — AcademicCheck AI

Date: 2026-09-07  
A01–A10 mapped to evidence. Unrun host items = FAIL for production.

| ID | Theme | Repo status | Evidence | Prod residual |
| --- | --- | --- | --- | --- |
| A01 Broken access control | Isolation 404, admin roles | **PASS pytest** | test_isolation | SEC-01 pentest |
| A02 Cryptographic failures | Argon2id, AES-GCM fields, HSTS if prod | **PARTIAL** | crypto tests | No TDE; dumps plaintext; TLS terminator unmeasured |
| A03 Injection | SQLAlchemy binds; upload/PDF/JS; prompt wrap | **PASS pytest** | document_security, prompt_injection, no raw SQL concat in API | Host SSRF unrun |
| A04 Insecure design | Capability share links; no MFA | **PARTIAL** | threat model | SEC-06, SEC-11 |
| A05 Misconfiguration | OpenAPI off in prod; sqlite refused | **PARTIAL** | lifespan | Debug off; CORS from settings |
| A06 Vulnerable components | pip-audit `\|\| true` | **FAIL CI gate** | ci.yml | SEC-03, SEC-04 |
| A07 Auth failures | Lockout, reuse, CSRF | **PASS pytest** | security_cert | Stuffing under rate limit |
| A08 Integrity | Webhook HMAC + event_id | **PASS pytest** | billing_critical | Live SEC-07 |
| A09 Logging failures | structlog + security_events + redaction | **PARTIAL** | logging.py | No SIEM (SEC-09) |
| A10 SSRF | Citation HTTP allow-list (prior) | **PARTIAL pytest** | citation verify | Host SSRF unrun |

**OWASP production audit: FAIL** (A06 gate + pentest + secrets).
