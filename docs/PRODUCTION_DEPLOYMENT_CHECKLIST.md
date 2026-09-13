# Production deployment checklist — AcademicCheck AI

Use this before sharing any staging or production URL.

## P0 — must pass

- [ ] `APP_ENV=staging` or `production` (never leave `development` publicly)
- [ ] `APP_DEBUG=false`
- [ ] PostgreSQL (not SQLite) with Alembic at head
- [ ] Redis reachable; at least one RQ worker registered
- [ ] `/api/live` returns 200
- [ ] `/api/ready` returns 200 (LB must use **ready**, not live)
- [ ] Secrets via platform env and/or `SECRETS_FILE` + `SECRET_MANAGER_URI` (see `docs/SECRETS_MANAGEMENT.md`)
- [ ] `JWT_SECRET_KEY` and `APP_SECRET_KEY` ≥ 32 random bytes
- [ ] `FIELD_ENCRYPTION_KEY` set and backed up offline
- [ ] `COOKIE_SECURE=true` behind HTTPS
- [ ] CORS / `APP_WEB_URL` locked to the real origin
- [ ] Payment keys **test-mode only** until live PSP drills complete — or hide checkout (`checkout_available=false`)
- [ ] `SENTRY_DSN` set (API) and `NEXT_PUBLIC_SENTRY_DSN` set (web)
- [ ] `ALERT_WEBHOOK_URL` or PagerDuty routing key set
- [ ] Automated Postgres backup scheduled + one restore drill evidenced (see `docs/LAUNCH_RECOVERY_RUNBOOK.md`)
- [ ] Smoke: register → check → report (Top 3 Critical Fixes) → PDF → coach

## P1 — before public free launch

- [ ] Object storage (S3/R2) for uploads if multi-node
- [ ] Image scan on deploy artifacts
- [ ] Staging distinct from production credentials
- [ ] Rollback path rehearsed (`ops/deploy_compose.sh` / prior image)
- [ ] About / Contact / Privacy / Integrity pages live
- [ ] No exaggerated accuracy or “official grade” claims

## P2 — before paid production

- [ ] Live Stripe/Paystack/Flutterwave charge + refund + webhook evidence pack
- [ ] Managed Postgres PITR (or equivalent RPO ≤ 5–15 min) with signed restore
- [ ] Independent pentest with no open High findings
- [ ] On-call owner named; alert pages a human

## Health probes

| Probe | Use |
| --- | --- |
| `/api/live` | Process up (may stay 200 during dependency loss) |
| `/api/ready` | Safe to receive traffic |
| `/api/metrics` | Ops counters |

## Soft-launch rule

Invite-only or private URL. Free/guest checks OK. **No live paid traffic** until P2 payment + backup gates pass.
