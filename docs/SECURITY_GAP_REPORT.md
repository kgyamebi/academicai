# Security Gap Report — AcademicCheck AI

Date: 2026-09-07  
Method: code + pytest, not documentation trust. Score remains **92 / 98**. Independent pentest: **not commissioned**.

Register: `docs/SECURITY_RISK_REGISTER.md`. Certification: `docs/SECURITY_CERTIFICATION.md`.

| Control | Implemented? | Tested? | Classification |
| --- | --- | --- | --- |
| Authentication | Yes | security_hardening / security_cert | PASS (repo) |
| Sessions / refresh reuse | Yes | persist before 401 | PASS (repo) |
| Authorization / isolation | Yes | test_isolation | PASS (repo only) |
| Encryption at rest (fields) | AES-GCM | crypto tests | PARTIAL (no TDE) |
| TLS | HSTS if production | terminator unmeasured | PARTIAL |
| Billing HMAC + replay | Yes | billing_critical | PARTIAL (no live keys) |
| Uploads | MIME/signature/zip/JS | document_security | PASS (repo) |
| Malware scanning | Optional ClamAV | not default | PARTIAL |
| Prompt injection | Firewall + 1000 cases | test_prompt_injection | PASS (synthetic) |
| Secret manager | SECRETS_FILE / env | not AWS/GCP SM | FAIL production |
| Admin MFA | TOTP enroll/challenge + admin API gate | `test_security_mfa_jwt.py` | PASS code; staging drill HAL-09 |
| Pentest / DAST / image scan | No | — | FAIL |
| pip-audit blocking | dedicated workflow only | ci.yml still `\|\| true` | FAIL main CI |

**Do not treat 92 as 98.** Critical/High operational items remain → production security **FAIL**.
