# Security Architecture — AcademicCheck AI

Date: 2026-09-07  
This describes **what is in the repository**. It is not a passing security certificate.

## Authentication

| Control | Implementation | Validated |
| --- | --- | --- |
| Argon2id | New password hashes; bcrypt still verifies; rehash on login | pytest |
| Refresh rotation | New refresh issued; old row revoked | pytest |
| Reuse detection | Family revoke **committed** before 401 | pytest (rotated token 401) |
| Password reset | One-time `SessionToken`; all sessions revoked on reset | pytest |
| Email verification | Required in staging/production | pytest (staging) |
| Session / device | `sessions.user_agent`, `ip_address`; new-IP security event | pytest |
| Logout / logout-all | Revoke refresh row(s); clear cookies | pytest |
| JWT rotation | `JWT_SECRET_PREVIOUS` accepted on decode; new tokens use current | pytest this pass |
| MFA | **Not shipped** (no TOTP/WebAuthn UI — product freeze) | Fail |

## Authorization

Fail-closed ownership on assignments, documents, analysis, reports, PDF, share, versions, coach, payments, admin (`require_roles`). Isolation suite: **100 in-repo**. Live-host IDOR: **unrun**.

## API / OWASP (in-repo)

CSRF cookies, clickjacking headers, payload caps, rate limits, SQLAlchemy (no string SQL for tenant IDs), upload signature/zip/JS guards, prompt wrap, DOI allow-list for Crossref (this pass). SSRF to metadata IPs via DOI: pytest. Independent pentest: **FAIL**.

## Secrets

- `.env` gitignored; production boot rejects default JWT/app/field keys.
- `SECRETS_FILE` JSON allow-list injection; missing file fails closed (pytest). **Not** AWS/GCP Secret Manager until that sidecar exists.
- Logs redact tokens and `sk_live_` / `sk_test_`.
- Rotation: `ops/rotate-secrets.md`.

## Encryption

Field crypto AES-256-GCM `enc:v2:`. Cookies HttpOnly. TLS 1.3 is **edge/host**, not measured here. Backups are plaintext `pg_dump` — **FAIL** encrypted backup.

## Monitoring

`SecurityEvent` rows: login fail/lockout, refresh_reuse, login_new_ip. No SIEM. Threat detection beyond these events: **FAIL**.
