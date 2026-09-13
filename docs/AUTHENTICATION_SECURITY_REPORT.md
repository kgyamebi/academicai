# Authentication Security Report — AcademicCheck AI

Date: 2026-09-09  
Evidence: `test_security_hardening.py`, `test_security_cert.py`, `test_security_mfa_jwt.py`, `test_security_lab_attacks.py`.

| Control | Status | Evidence |
| --- | --- | --- |
| Argon2id hashing | PASS repo | hash_password / rehash on login |
| Breach denylist (local) | PASS repo | expanded `_COMMON_PASSWORDS`; not live HIBP API |
| Strong password policy | PASS repo | letters+numbers, min 8, denylist |
| Email verification | PASS when configured | prod/staging login gate |
| Password reset single-use | PASS repo | SessionToken consume |
| Refresh rotation | PASS repo | revoke + issue |
| Refresh reuse detection | PASS repo | family revoke commits before 401 |
| Session revocation / logout-all | PASS repo | |
| Device-aware (new IP event) | PASS repo | `login_new_ip` |
| Concurrent session limit | PASS repo | `max_refresh_sessions` (default 10) |
| Account lockout | PASS repo | 8 / 15 min |
| Credential stuffing / brute force | PARTIAL | lockout + rate limit; Redis required in prod |
| MFA TOTP privileged | PASS code | enroll/challenge/admin gate; **staging UI HAL-09** |
| JWT alg allow-list | PASS repo | rejects alg=none / wrong HS |

**Certification: PASS (repository).** **FAIL (production auth)** without pentest + MFA staging drill + secret manager for JWT material.
