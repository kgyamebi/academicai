# Security audit — AcademicCheck AI

Date: 2026-09-09 (Security architecture continuation)  
Method: code review + pytest. **No independent penetration test and no live-host attack were executed.**

Target: 98 / 100. Evidence-backed score after this pass: **94 / 100**. Gate: **Fail** (caps: pentest, secret manager, live PSP).

---

## Attack surface report

| Surface | Entry points | Trust boundary |
| --- | --- | --- |
| Public web | `/`, marketing, login, register, verify, reset, shared reports | Unauthenticated HTML; share token is a capability |
| Auth API | `/api/auth/*` | Cookies + CSRF; JWT in HttpOnly cookies or Bearer |
| Tenant API | assignments, documents, analysis, reports, PDF, coach, dashboard, versions | `get_current_user` + ownership queries |
| Billing API | checkout, credits, payments, cancel | Server-side plan/pack prices; signed webhooks |
| Admin API | `/api/admin/*` | `require_roles("admin")` |
| Uploads | `/api/documents/upload`, paste | Magic bytes, size, zip/PDF checks, then store under `{user_id}/` |
| AI | enhance + coach via provider HTTP | System prompt + layered untrusted wrappers; output sanitizer |
| Storage | local disk or S3 | Key traversal rejected; S3 SSE-AES256 + optional signed GET |
| Webhooks | Stripe / Paystack / Flutterwave | Signature + replay table; unmatched actionable → 503 |

Frontend never authorizes resources. Path IDs, query IDs, and body IDs are not trusted.

---

## Vulnerability report (this pass)

### Closed or reduced in code

| ID | Severity | Finding | Mitigation | Proof |
| --- | --- | --- | --- | --- |
| AUTH-01 | High | Password hashes were bcrypt-only | Argon2id for new hashes; bcrypt still verifies; rehash on login | `test_security_hardening.py` |
| AUTH-02 | High | Reset/verify JWTs were reusable | One-time `SessionToken` consume | `test_reset_token_is_single_use` |
| AUTH-03 | High | Refresh rotation race / reuse not persisted | `SELECT … FOR UPDATE`; reuse **commits** family revoke before 401 | `test_refresh_reuse_is_rejected` (rotated token 401) |
| AUTH-04 | Medium | Login user enumeration timing | Dummy password check on unknown accounts | `dummy_password_check` |
| AUTH-05 | Medium | Weak / common passwords | Policy rejects common and alpha-only; `password12` still valid | `test_password_policy_*` |
| AUTH-06 | Medium | Email verification optional in prod | Login blocked in production/staging until verified | `test_login_requires_verification_when_configured` |
| AUTH-07 | Medium | No multi-device logout | `POST /api/auth/logout-all` | `test_logout_all_revokes_refresh` |
| A01 | High | Report `page_size` unbounded | `Query(le=100)` | `test_report_page_size_is_capped` |
| A01 | Medium | Admin plan/flag mass assignment | Pydantic allow-list schemas | `test_admin_flag_schema_rejects_unsafe_keys` |
| A02 | High | Field crypto was Fernet-only | New writes AES-256-GCM `enc:v2:`; `enc:v1:` still decrypts | `test_encrypt_uses_aes256_gcm_and_reads_legacy_fernet` |
| A02 | Medium | Gemini key in query string | `x-goog-api-key` header | `provider.py` |
| A02 | Medium | Console email printed JWTs | Token redaction; console refused in production | `test_console_email_redacts_tokens` |
| A05 | Medium | Share unlock unrated | `share` rate-limit bucket | `rate_limit.py` |
| A06 | Low | Upload polyglot / macros / JS | Double-ext, DOCX macro/OLE parts, PDF `/JavaScript` `/Launch` | `test_document_security.py` |
| A10 / AI | High | Document text could sit in the user layer | `wrap_layers` SYSTEM > USER > DOCUMENT > REFERENCE on enhance/coach | `test_prompt_injection.py` |
| BILL-01 | High | Unmatched webhooks marked processed | Actionable unknown payment → 503, unprocessed | `test_paystack_webhook_accepts_valid_hmac` |
| AUTH-09 | High | No MFA for privileged roles | TOTP MFA + backup codes; privileged login enroll/challenge; admin API requires `mfa_enabled` | `test_security_mfa_jwt.py`, `test_mfa_and_recovery.py` |
| AUTH-10 | High | JWT alg=none / confusion | `decode_token` allow-lists configured HS* only; requires `exp`/`sub`/`typ` | `test_jwt_rejects_alg_none` |
| BILL-03 | Medium | Reconcile not scheduled/alerted | CLI + workflow + alert on mismatch; empty fixture for CI smoke | `ops/run_billing_reconcile.py`, `test_billing_reconcile_alert.py` |

### Open (not closed by this pass)

| ID | Severity | Finding | Why it remains |
| --- | --- | --- | --- |
| AUTH-08 | Medium | Register still issues a first session | Existing onboarding; login after logout requires verify in prod. Closing this needs a frontend redirect change. |
| AUTH-09b | Medium | MFA UI / staging login drill | Backend code-complete; HAL-09 needs staging login proof + product UI polish |
| A05 | High until drill | Secrets live in env / `.env`, not a manager | Host change |
| A05 | Medium | Main `ci.yml` still has `pip-audit … \|\| true` | Weekly `security-scan.yml` is blocking; HAL-24 for main CI |
| A06 | Medium | ClamAV optional; absent in prod rejects uploads only if `CLAMAV_HOST` set | Operator config |
| A09 | Low | Unhandled errors log `str(exc)` | Redaction processor covers secret keys; not a full DLP |
| SHARE-01 | Low | Share token is a capability URL | 24-byte urlsafe; leak = read |
| AI-01 | Medium | Prompt injection residual | Firewall + wrap; models can still leak style |
| BILL-02 | High until drill | Live Stripe/Paystack/Flutterwave uncertified | No live keys here |
| PEN-01 | High | No independent pentest | Pytest ≠ host attack |

---

## Security risk register

| Risk | Likelihood | Impact | Score | Treatment | Owner |
| --- | --- | --- | --- | --- | --- |
| Cross-tenant draft/report leak | Low in repo tests | Critical | Medium until pentest | Isolation suite; fail-closed 404 | Security |
| Credential stuffing / brute force | Medium | High | Medium | Lockout 8/15 min, rate limits, Argon2id | Auth |
| Malicious upload (macro/JS/zip bomb) | Medium | High | Medium | Signature + zip/PDF guards; ClamAV optional | Upload |
| Prompt injection → policy override | Medium | High | Medium | Layered prompts + output sanitizer | AI |
| Webhook replay / unmatched grant | Low in code | Critical | High until live drill | HMAC + idempotency + 503 | Billing |
| Secret leak from disk `.env` | Medium if deployed that way | Critical | High | Require secret manager at deploy | SRE |
| Share-link leakage | Low | Medium | Low | Revoke + password + expiry | Product |
| Admin session on shared device | Low | High | Low–Medium | MFA enrolled + required for admin API; staging drill pending | Auth |

---

## OWASP Top 10

| Control | Status | Tests |
| --- | --- | --- |
| A01 Broken access control | Mitigated in repo (ownership on assignments, documents, reports, versions, payments, credits, subscriptions, jobs, coach, PDF, notes, share, admin) | `test_isolation.py` |
| A02 Cryptographic failures | AES-256-GCM at rest when `FIELD_ENCRYPTION_KEY` set; TLS is host; cookies HttpOnly / Secure in prod / SameSite=Lax | `test_crypto_time_metrics.py`, `test_security_cert.py` |
| A03 Injection | Parameterized SQLAlchemy; upload not executed; admin schemas | isolation + document + admin schema tests |
| A04 Insecure design | Fail-closed 404 on IDOR; webhooks fail closed; email verify on prod login | hardening + isolation |
| A05 Security misconfiguration | OpenAPI off in prod; HSTS in prod; Redis rate limit fails closed in prod | `test_hardening.py` |
| A06 Vulnerable components | Dependencies pinned by lower-bound; `pip-audit` not a release gate | residual |
| A07 Authentication failures | Argon2id, lockout, refresh rotation/reuse, one-time reset/verify, dummy timing, password policy, privileged MFA | `test_security_hardening.py`, `test_security_cert.py`, `test_security_mfa_jwt.py` |
| A08 Integrity failures | Webhook signatures; no frontend payment amounts | billing tests |
| A09 Logging failures | Security events table; log key redaction; tokens stripped from console email | hardening tests |
| A10 SSRF | Provider URLs hardcoded; Gemini key not in URL | `provider.py` review |

---

## Phase notes (what was in scope vs not)

**Auth.** Argon2id, reset single-use, prod login verification, refresh lock, device IP new-login event, logout-all, lockout, rate limits, password policy. **MFA (code-complete):** encrypted TOTP + hashed backup codes; privileged login returns enroll or challenge tokens (no access session until MFA); `/api/admin/*` requires `mfa_enabled`. Staging UI drill remains HAL-09.

**Authorization / isolation.** Server-side `user_id` match; fail closed 404. Isolation 100 is the **repository suite only**.

**Uploads.** Magic bytes, MIME assist, size, page/extract limits, zip bomb, path, double extension, DOCX macros/OLE, PDF JS/Launch. Rejected files are **not stored** (no malware quarantine directory). Signed GET exists for S3.

**API.** Rate limits, pydantic schemas, pagination caps, payload field limits, webhook idempotency. Request signing of client APIs was **not** added (new client contract).

**Secrets.** No live provider secrets in `backend/app`. `.env` is local-only and must not be committed. Git history rewrite was **not** performed. Deploy must inject from a secret manager.

**Encryption.** New sensitive fields use AES-256-GCM (`enc:v2:`). Transit TLS 1.3 is a host/load-balancer setting, not proven here.

**AI.** Uploaded/pasted content is wrapped as untrusted data. Injection suite ≥ 1000 cases. Residual model-level risk remains.

**Billing.** Server is authoritative. Signed webhooks, replay table, unmatched 503.

---

Honest security score: **94**. Not 98: no pentest, no secret manager, MFA staging/UI drill pending, register first-session residual, ClamAV not mandatory, main CI pip-audit still non-blocking, live billing uncertified, TLS terminator unproven.
