# Security Report — AcademicCheck AI

Date: 2026-09-07  
Standard requested: enterprise production SaaS  
Evidence-backed score: **92 / 100.** Gate 98. **Fail.**  
Pentest: **not commissioned.** Secret manager: **not used.** Admin MFA: **not implemented.**

This pass (code only): `SECRETS_FILE` injection (pytest); `JWT_SECRET_PREVIOUS` rotation decode (pytest); unsafe DOI rejected before Crossref HTTP (pytest). Refresh family revoke remains from prior pass.

## Controls present (pytest)

| Area | Control | Evidence |
| --- | --- | --- |
| Authn | Argon2id new hashes; bcrypt verify + rehash | `test_security_hardening.py` |
| Authn | Refresh rotation + reuse family kill + logout-all | `test_security_cert.py` |
| Authn | Lockout 8 failures / 15 min | `test_lockout_after_repeated_failures` |
| Authn | Device fields on `sessions` | UA/IP columns + login test |
| Authz | Ownership fail-closed 404 | `test_isolation.py` |
| Authz | Admin role isolation | isolation + admin tests |
| API | Rate limits (Redis; prod fail-closed) | `rate_limit.py` |
| API | Payload caps, CSRF, security headers | cert + hardening tests |
| Files | MIME/signature, zip bomb, JS/macro PDF | `test_document_security.py` |
| Files | ClamAV if `CLAMAV_HOST` | optional; **not** a quarantine store |
| AI | Untrusted wrappers; output sanitizer | `test_prompt_injection.py` |
| Crypto | TLS is **host**; AES-256-GCM `enc:v2:` fields | `test_encrypt_uses_aes256_gcm_*` |
| Billing webhooks | HMAC + replay table | `test_billing_critical.py` |

## Not implemented / failed

| Item | Status |
| --- | --- |
| Independent pentest | **FAIL** — no host attack |
| Secret manager | **FAIL** — env files |
| MFA / admin step-up | **FAIL** — no TOTP/WebAuthn product (intentionally not added) |
| Live webhook abuse | **FAIL** — keys absent |
| Encrypted backups | **FAIL** — dump is plaintext `pg_dump` |
| TLS 1.3 | **FAIL** as a product cert — not measured on a deployed terminator |
| Malware quarantine bucket | **FAIL** — fail-closed reject only |
| Register first-session | Open (onboarding workflow freeze) |

## Decision

**NOT READY FOR PRODUCTION** on security. Code controls are real. Host, pentest, MFA, and secret manager are not.
