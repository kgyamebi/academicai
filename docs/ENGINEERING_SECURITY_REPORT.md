# Security Improvement Report — AcademicCheck AI

Date: 2026-09-07  
Score: **92 / 100**. Gate 98. **Fail.**  
Full control list: `docs/SECURITY_REPORT.md`. This document records the engineering-quality pass only.

## This pass (quality, not new product controls)

| Item | Location | Result | Evidence |
| --- | --- | --- | --- |
| Report PDF/share/revoke ownership in SQL | `reports.py` `_owned_report` | Pass | isolation suite re-run + source tests |
| Share scores not lazy-loaded across tenants | `_shared_report` | Pass | source assert |
| Validation 422 does not echo internals | `main.py` | Pass | `test_validation_errors_do_not_echo_internals` |
| 401/500 bodies have no traceback | handlers | Pass | `test_http_errors_are_structured` |
| OpenAPI off in production | `main.py` `_docs_enabled` | Unchanged | code |

No MFA UI, no pentest, no AWS/GCP secret manager, no encrypted backups were added (product/infra freeze + no mock unpaid services).

## Existing controls (not re-tested as a pentest)

Argon2id, refresh family revoke + persist before 401, AES-256-GCM fields, CSRF, security headers, upload MIME/JS/macro guards, DOI allow-list, `SECRETS_FILE` allow-list, `JWT_SECRET_PREVIOUS`, webhook HMAC + replay. See `tests/test_security_cert.py`, `tests/test_storage_and_secrets.py`.

## Least privilege / audit

- Admin routes role-gated.
- Share access logged (`ShareAccessLog`).
- Security events table (Alembic 003) used for refresh reuse.

## Remaining attack surface (open)

| Item | Status |
| --- | --- |
| Independent pentest | Not commissioned |
| Secret manager | Env / optional `SECRETS_FILE` JSON — not AWS SM / GCP SM |
| Admin MFA | Not implemented |
| Live webhook abuse | Keys absent (`ops/cert_payment_keys.json`) |
| Encrypted `pg_dump` | Plaintext local dumps |
| TLS terminator proof | Not measured on a deployed host |

## Verdict

Repo security tests remain the 92 evidence pack. This pass tightens report query authorization and error leakage. **Not** 98.
