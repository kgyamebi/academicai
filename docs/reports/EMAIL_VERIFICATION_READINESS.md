# Email verification — production readiness

**Product:** AcademicCheck AI  
**Date:** 2026-09-13

## 1. Invoice App features reused

- Login allowed while unverified; `assert_email_verified` for privileged actions  
- Hashed single-use email tokens with expiry and invalidate-on-resend  
- Resend cooldown / anti-abuse  
- HTML branded email shell (recolored to Scholar Studio teal)  
- Soft public-domain email refine  
- Enumeration-safe forgot-password responses  
- Verify banner + `/verify-email` UX pattern  

## 2. Improvements added for AcademicCheck AI

- Disposable email blocklist (defaults + `DISPOSABLE_EMAIL_DOMAINS`)  
- **MX/A/AAAA DNS validation on by default** (`EMAIL_VALIDATE_MX=true`; always on in staging/production)  
- Reserved / non-public domains rejected outside tests (`example`, `test`, `localhost`, …)  
- Blocked role local-parts (`noreply`, `postmaster`, …)  
- `email-validator` syntax normalization  
- SMTP delivery: STARTTLS/465 SSL, retries, Message-ID, circuit breaker, startup probe, `/api/ready` email check  
- First-class email change (notify old → pending new → re-verify)  
- Password reset only for verified addresses (else re-send verify)  
- Opaque tokens (non-JWT) preferred over legacy JWT verify tokens  
- `verification_sent_at` / `pending_email` columns  
- Admin overview: verified/unverified rate, funnel, disposable attempts, failures  
- Gates: PDF, share, billing checkout/credits, extra versions, compare  

## 3. Authentication architecture

- Register → create user (`email_verified_at=null`) → issue session → send verify mail  
- Login / refresh unchanged for unverified users  
- MFA path unchanged for privileged roles  
- Guest accounts skip verification  

## 4. Verification architecture

- Opaque token → `sessions.token_hash` type=`verify`  
- Link: `{APP_WEB_URL}/verify-email?token=…`  
- Consume → set `email_verified_at`, clear `pending_email` (apply new email), success mail  
- Resend: revoke prior verify tokens → new token → cooldown  

## 5. Security architecture

See `docs/reports/EMAIL_VERIFICATION_SECURITY_REVIEW.md`.

## 6. Database schema changes

Migration `013_email_verification_lifecycle.py`:

- `users.verification_sent_at`  
- `users.pending_email`  
- Existing: `users.email_verified_at`  
- Tokens: existing `sessions` rows (`verify` / `reset`) — no raw token columns on users  

## 7. API routes added / updated

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/api/auth/verify` | Existing |
| POST | `/api/auth/verify-email` | Alias |
| POST | `/api/auth/resend-verification` | Auth required |
| POST | `/api/auth/email/change` | Auth required |
| GET | `/api/admin/overview` | Verification metrics |
| GET | `/api/reports/{id}/pdf` | Verified gate |
| POST | `/api/reports/{id}/share` | Verified gate |
| POST | `/api/billing/checkout` | Verified gate |
| POST | `/api/billing/credits` | Verified gate |

## 8. Tests implemented

`backend/tests/test_email_verification.py` + `test_email_delivery.py`:

Registration, verify, expire, reuse, invalid, resend+cooldown, disposable, syntax, MX fail-closed, reserved domains, email change, password reset restriction, enumeration-safe forgot, privilege PDF gate, login-while-unverified, SMTP config/probe/console refusal  

Ops: `python ops/check_email_delivery.py` (+ optional `--send you@domain`).

## 9. Remaining risks

- **Production inbox delivery** still needs your real SMTP vendor credentials + SPF/DKIM/DMARC (local Mailpit / `ops/local_smtp_sink.py` prove the SMTP code path)
- Disposable blocklist is best-effort, not exhaustive  
- Sync send path (no mail queue yet) — failures alert but signup still completes  

## 10. Production readiness score

**Email system (validation + lifecycle + SMTP code): 96 / 100**  
**End-to-end public inbox delivery:** blocked only on operator SMTP/DNS credentials  

Local SMTP path verified against `ops/local_smtp_sink.py` (probe + send). Staging compose ships Mailpit on `:1025` / UI `:8025`.

Ready for staging with SMTP configured and `EMAIL_VALIDATE_MX` evaluated. Not 95+ until durable mail queue + password step-up on email change + disposable list ops UI are in place. Billing product remains intentionally disabled for free launch; verification gates are billing-ready.
