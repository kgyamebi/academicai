# Invoice App vs AcademicCheck AI — Auth & Email Verification

**Date:** 2026-09-13  
**Sources:** `C:\Users\Administrator\Desktop\invoice app\invoiceapp` · `aiessayassignmentchecker`

## Executive summary

Invoice App is the reference for **verification lifecycle, hashed tokens, resend, HTML mail, audit actions, and gating privileged features while allowing login**. AcademicCheck keeps JWT sessions, hashed one-time tokens via `sessions`, lockout, and MFA — and now **matches Invoice on login+gates**, with HTML mail, resend, disposable/MX, and email-change.

**Reuse Invoice patterns; keep AcademicCheck session/JWT architecture; improve email quality controls.**

---

## Side-by-side

| Area | Invoice App | AcademicCheck AI (before) | Decision |
| --- | --- | --- | --- |
| Authentication | Cookie session JWT + hashed session row | Access/refresh JWT + hashed refresh rows | **Keep AC** (stronger refresh reuse revoke) |
| Email verification flag | `emailVerifiedAt` | `email_verified_at` | **Reuse concept** (already present) |
| Token storage | `EmailToken` (hash, type, usedAt, expires) | `SessionToken` type=`verify`/`reset` | **Adapt Invoice** onto existing `sessions` table |
| Token security | `randomToken` + `hashToken`, single-use claim | JWT create + hash store + revoke | **Improve**: opaque random + hash (Invoice), keep expiry |
| Registration | Create user → token → enqueue verify + welcome | Create user → JWT verify token → console/SMTP text | **Adapt** Invoice flow + HTML templates |
| Login unverified | **Allowed**; banner + `assertEmailVerified` for send/pay | **Blocked** when `require_email_verification` | **Match Invoice** (allow login, gate features) |
| Feature gate | Invoices, invites, checkout | (none / login wall) | **Adapt**: PDF, share, billing for unverified |
| Resend | Invalidate unused + rate limit 5/min IP | Missing | **Reuse Invoice pattern** |
| Password reset | Always `{ok:true}`; send if exists | Always silent; no verified check | **Improve**: only reset if verified; else re-send verify (no enumeration) |
| Email change | Not found as first-class flow | Missing | **New** (AC improvement) |
| Email delivery | Queue + Resend/SMTP + templates | Console/SMTP sync text | **Adapt templates**; keep AC providers |
| Audit | `writeAudit` auth.* actions | `SecurityEvent` | **Reuse AC SecurityEvent** with Invoice action names |
| Rate limiting | Per-route `rateLimit` | `check_rate_limit` buckets | **Reuse AC** + add verify-resend bucket |
| Disposable email | Not implemented | Missing | **New AC improvement** (admin-configurable) |
| MX / DNS | Soft “public domain” refine only | Missing | **Improve**: soft domain + optional MX |
| Email templates | Branded HTML wrap | Plain text | **Adapt Invoice wrap** → Scholar Studio teal |
| Admin metrics | Verified % in CS/executive | Users count only | **Add** verified/unverified/funnel |
| Session handling | Session revoke list | Refresh family revoke on reuse | **Keep AC** |
| MFA | TOTP + passkeys | TOTP for privileged | **Keep AC** |

---

## What can be reused directly (pattern / logic)

1. **Allow login + gate privileges** (`assertEmailVerified`) — Invoice `src/server/auth.ts`
2. **Resend**: invalidate unused VERIFY tokens → new token → rate limit — `resend-verification/route.ts`
3. **Verify claim**: atomic `usedAt` update — `verify-email/route.ts`
4. **HTML email shell** — `lib/email/templates.ts` (rebrand colors)
5. **Banner UX** — `email-verify-banner.tsx`
6. **Soft email domain refine** — `lib/validation.ts` `hasPublicEmailDomain`
7. **Register audit** — `auth.register` / `auth.email.verified` / `auth.email.verification_resent`

## What should be adapted

| Invoice | AcademicCheck adaptation |
| --- | --- |
| Prisma `EmailToken` | `SessionToken` with types `verify` / `reset` (+ revoke = used) |
| `enqueueEmail` queue | Sync `send_email` (+ HTML multipart) until AC has a mail queue |
| Next.js routes | FastAPI `/api/auth/*` |
| Blue brand `#0A5FFF` | Teal Scholar Studio `#0f766e` |
| Gate “send invoices” | Gate PDF / share / billing checkout |

## What should be improved (AC ahead of Invoice)

1. Disposable email blocklist (admin-configurable env + defaults)
2. Optional MX lookup (fail-open in dev; configurable fail-closed in prod)
3. Explicit email-change flow (notify old + re-verify new)
4. Password reset only for verified; unverified gets verify mail (enumeration-safe)
5. Opaque verification tokens (not JWT) hashed at rest — clearer single-use semantics
6. `verification_sent_at` on user for cooldown UX
7. Richer `/verify-email` success/expired/failed UI states

## What should remain unchanged

- Refresh-token reuse detection / session family revoke  
- Argon2 password hashing + lockout  
- MFA for privileged roles  
- Guest flow (no email verification)  
- CSRF cookie model  
- Billing intentionally disabled for public free launch (gates still prepare for paid)

---

## Target architecture (post-change)

```
Register → validate email (syntax + domain + disposable [+ MX])
        → create user (email_verified_at=null)
        → issue opaque verify token (hash in sessions)
        → send HTML verify email
        → issue session (login allowed)

Login    → allowed if password OK (even if unverified)
        → client shows VerifyEmailBanner

Privileged actions (PDF, share, billing) → assert_email_verified()

Verify   → hash token → consume once → set email_verified_at
Resend   → cooldown + rate limit → invalidate old → new token + email
```
