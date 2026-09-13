# Public Free Launch — Go Live Checklist

Billing is intentionally disabled. Do not enable Stripe/Paystack for this release.

## Pre-flight (host)

- [ ] `APP_ENV=production` (or equivalent) and `APP_DEBUG=false`
- [ ] `COOKIE_SECURE=true` behind HTTPS only
- [ ] Postgres reachable; migrations applied through latest Alembic head
- [ ] Redis reachable; at least one RQ worker running
- [ ] Object storage (or local storage policy) configured for uploads
- [ ] `SENTRY_DSN` and `NEXT_PUBLIC_SENTRY_DSN` set (or consciously deferred with owner sign-off)
- [ ] `ALERT_WEBHOOK_URL` pages a human for ready/worker failures
- [ ] Secrets only via host secret manager / `SECRETS_FILE` — no committed `.env` with live keys
- [ ] Domain + TLS certificate valid; HSTS/security headers verified on the public URL

## Health

- [ ] `GET /api/live` → 200
- [ ] `GET /api/ready` → 200 (DB + Redis + queue policy)
- [ ] Frontend `/` and `/check` load over HTTPS
- [ ] Worker heartbeat / queue depth not stuck

## Product smoke (happy path)

1. Register → login
2. Upload PDF/DOCX or paste draft on `/check`
3. Analysis completes → Academic Performance Overview
4. Dashboard shows score / recent report
5. Coach opens with assignment context
6. PDF download (if feature flag on) succeeds or fails gracefully
7. Sign out → sign in → reopen previous report by URL

## Failure path smoke

- [ ] Invalid file type shows inline error (no silent drop)
- [ ] Oversized file rejected with clear message
- [ ] Expired session redirects/prompts sign-in without infinite skeletons
- [ ] Worker kill during analysis → user sees failed state + retry / dashboard recovery
- [ ] Billing page shows **Purchases unavailable** — no checkout buttons

## Trust pages

- [ ] `/terms`, `/help/privacy`, `/security`, `/about`, `/contact`, `/help` present
- [ ] No guaranteed-grade / fake testimonial / fake stats claims

## Free-launch gates

- [ ] App nav has **no Billing** item (Settings only)
- [ ] `/pricing` explains free public launch
- [ ] `/app/billing` is usage-only; purchases disabled in UI
- [ ] Dashboard has no upgrade pressure CTAs

## Rollback

- [ ] Previous container/image tag known
- [ ] DB backup / restore path documented (`docs/LAUNCH_RECOVERY_RUNBOOK.md`)
- [ ] Feature flag or traffic switch to take `/check` offline if needed

## Sign-off

| Role | Name | Date | Go / No-go |
|------|------|------|------------|
| Engineering | | | |
| Product | | | |
| Ops / SRE | | | |

**Verdict target:** PUBLIC FREE LAUNCH (not paid production).
