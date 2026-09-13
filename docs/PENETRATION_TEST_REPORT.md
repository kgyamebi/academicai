# Penetration Test Report — AcademicCheck AI

Date: 2026-09-09  

## Independent pentest

**FAIL — not executed.** HAL-07 remains open. Pytest ≠ ASVS pentest.

## Lab simulated attacks (repository)

Suite: `tests/test_security_lab_attacks.py` + isolation/hardening/MFA/JWT/document/prompt suites.

| Attempt | Lab result |
| --- | --- |
| IDOR assignment | 404 |
| Unauthenticated mutation | 401/403 |
| JWT alg=none | rejected |
| Privilege escalation student→admin | 403 |
| Refresh reuse | family revoke |
| Upload polyglot/macro/JS | rejected |
| Prompt injection synthetic | wrapped |
| Webhook forgery | signature fail (billing tests) |
| CSRF without session auth | denied |

**Lab: useful regression evidence.** **Certification: FAIL** for penetration testing.
