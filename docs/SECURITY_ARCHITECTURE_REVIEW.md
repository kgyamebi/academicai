# Security Architecture Review — AcademicCheck AI

Date: 2026-09-09  
Roles: Security Architect / AppSec / IAM / API / Cloud / OWASP / SaaS Auditor.  
Method: code review + pytest. **No independent host penetration test.**

## Trust boundaries

| Boundary | Untrusted side | Trusted side |
| --- | --- | --- |
| Browser / Next.js | All DOM, localStorage, query strings, client JWT if Bearer | HttpOnly cookies + server session validation |
| Public API | Path/body/query IDs, uploads, share tokens | `get_current_user`, ownership queries, CSRF |
| Webhooks | Provider HTTP | HMAC + replay table; fail-closed unmatched |
| Workers | Job IDs from Redis | Re-load job from DB; user_id from row |
| AI provider | Model output | Layered prompts + output sanitizer |
| Object storage | Keys from clients | Path traversal reject; `{user_id}/` prefix |
| Admin | Same network as API | `require_roles("admin")` + MFA enabled |

## Attack surface

Public web, `/api/auth/*`, tenant APIs, billing + webhooks, admin, uploads, AI enhance/coach, Redis RQ, email links (verify/reset), share capability URLs, metrics (if exposed).

## Risk summary

| Severity | Count (open) | Themes |
| --- | ---: | --- |
| Critical | 3 | No independent pentest; secrets not in managed vault in prod evidence; live PSP unsigned |
| High | 5 | ClamAV optional; main CI pip-audit non-blocking; MFA staging drill open; plaintext dump offsite custody; host TLS unmeasured |
| Medium | 4 | Register issues first session; fingerprint≠full-row; share capability URL; prompt residual |
| Low | 2 | Error `str(exc)` logging; dual dump formats |

## Security debt

- HAL-07 pentest, HAL-08 secret manager, HAL-09 MFA staging UI, HAL-12 ClamAV mandatory, HAL-24 blocking supply-chain in main CI.
- Docs historically said “MFA FAIL” — **code is present**; staging proof still open.

## Gaps closed this pass (engineering)

- Expanded local breached-password denylist + min length 8.
- Concurrent refresh session limit (`max_refresh_sessions`, default 10).
- Lab attack suite `test_security_lab_attacks.py`.
- Secrets allow-list includes `BACKUP_ENCRYPTION_KEY`.

## Verdict

**Architecture is enterprise-oriented in-repo.** Production enterprise SaaS certification: **FAIL** until Bucket B items close.
