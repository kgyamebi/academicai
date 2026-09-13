# Email verification security review — AcademicCheck AI

**Date:** 2026-09-13  
**Baseline:** Invoice App auth/email system  
**Scope:** Registration, verification tokens, resend, email change, password reset, feature gates

## Summary

AcademicCheck AI now matches Invoice App’s **login-allowed + privilege-gated** model, and exceeds it on disposable email blocking, optional MX checks, email-change lifecycle, and opaque hashed tokens stored in `sessions`.

## Controls verified

| Control | Status | Notes |
| --- | --- | --- |
| Cryptographically random tokens | Pass | `secrets.token_urlsafe(32)` |
| Tokens hashed at rest | Pass | SHA-256 via `hash_token`; raw never stored |
| Single-use / replay prevention | Pass | Consume sets `revoked_at`; reuse fails |
| Expiration | Pass | `email_verification_hours` (default 24) |
| Account enumeration (forgot) | Pass | Uniform success message |
| Unverified password reset | Pass | No reset mail; optional re-send verify |
| Disposable email block | Pass | Built-in list + `DISPOSABLE_EMAIL_DOMAINS` |
| Reserved domain soft reject | Pass | Invoice-style; skipped in `APP_ENV=test` |
| MX validation | Optional | `EMAIL_VALIDATE_MX`; fail-closed when on |
| Resend cooldown + rate limit | Pass | Per-user cooldown + `verify` bucket |
| CSRF | Pass | `/api/auth/verify*` exempt for email CTA POSTs |
| Feature gates | Pass | PDF, share, checkout, credits, version+, compare |
| Audit events | Pass | `SecurityEvent` types listed below |
| Secure cookies / refresh reuse | Unchanged | Existing AC session security retained |

## Audit events

`account_created`, `verification_sent`, `verification_resent`, `verification_completed`, `verification_failed`, `email_changed`, `password_reset_requested`, `password_reset_blocked_unverified`, `password_reset_completed`, `disposable_email_attempt`

## Residual risks

1. **MX disabled by default** — fake domains with valid syntax can still register until `EMAIL_VALIDATE_MX=true` in staging/prod.
2. **Disposable list is not exhaustive** — attackers rotate providers; admins must extend `DISPOSABLE_EMAIL_DOMAINS` or add a feed later.
3. **Sync SMTP** — no durable mail queue yet (Invoice uses enqueue); console provider in dev can hide delivery failures.
4. **Email change leaves old address as login until verify** — intentional (pending_email); if attacker controls session they can lock the user into pending state until cooldown — mitigate with password re-auth on change (future).
5. **Privilege gates off in `APP_ENV=test`** — intentional for suite speed; staging/development/production gate on.

## Recommendations before public scale

- Enable `EMAIL_VALIDATE_MX=true` behind monitoring for false positives on academic domains.
- Add password confirmation for email change.
- Move verification/reset mail to a retrying queue.
- Admin UI to edit disposable domains (currently env-config).
