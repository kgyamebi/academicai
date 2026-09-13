# OWASP Compliance Report — AcademicCheck AI

Date: 2026-09-09  

| Control | Repo status | Residual |
| --- | --- | --- |
| A01 Broken access control | Mitigated (ownership + admin RBAC/MFA) | Host pentest open |
| A02 Cryptographic failures | Argon2id; AES-GCM enc:v2; dump encrypt optional | TLS edge unmeasured; vault open |
| A03 Injection | SQLAlchemy params; upload not executed | Residual parser bugs possible |
| A04 Insecure design | Fail-closed webhooks/IDOR | — |
| A05 Misconfiguration | OpenAPI off prod; HSTS/CSP headers | ClamAV optional |
| A06 Vulnerable components | security-scan.yml blocking; ci.yml `\|\| true` | HAL-24 |
| A07 Auth failures | Lockout, rotation, MFA code, session limit | Staging MFA drill |
| A08 Integrity | Webhook signatures | Live keys open |
| A09 Logging | security_events + redaction | SOC/pager open |
| A10 SSRF | Provider URLs constrained; DOI checks | Residual |

**OWASP production compliance: FAIL** (A06 main CI, pentest, vault, TLS proof).
