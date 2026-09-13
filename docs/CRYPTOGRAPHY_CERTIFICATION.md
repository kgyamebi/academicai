# Cryptography Certification — AcademicCheck AI

Date: 2026-09-07  
Tests: `test_crypto_time_metrics.py`, `test_storage_and_secrets.py`, security hardening.

| Item | Implementation | Tests | Prod validation |
| --- | --- | --- | --- |
| Passwords | Argon2id (id) time=3 memory=65536 parallel=2; bcrypt legacy | argon2/bcrypt tests | PASS repo |
| Tokens | JWT HS* with `jwt_algorithm`; jti | decode previous key | JWT ≥32 bytes enforced deploy |
| Token at rest | SHA-256 hash of refresh | hash_token | PASS |
| Cookies | HttpOnly + SameSite=Lax + Secure in prod | source | TLS terminator **unmeasured** |
| Field encryption | AES-256-GCM `enc:v2:` + AAD; Fernet v1 decrypt | crypto tests | Key required in production |
| Backups | gzip pg_dump **not** encrypted | — | **FAIL** SEC-08 |
| Secrets in git | `.env` gitignored | — | Process, not a scanner pass |
| TLS 1.3 | HSTS header if `is_production` | header code | **FAIL** handshake not captured |
| Key rotation | `JWT_SECRET_PREVIOUS` | decode loop | Procedure `ops/rotate-secrets.md` **un-drilled live** |
| Transit | HTTPS assumed at edge | — | Unmeasured |
| Rest (volume) | none (no TDE proof) | — | **FAIL** disk encryption unproven |

**Certification: PASS application crypto unit tests. FAIL** TLS/TDE/backup encryption as a platform.
