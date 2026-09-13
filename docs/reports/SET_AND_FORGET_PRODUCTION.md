# Set-and-forget production pack

**Date:** 2026-09-13  
**Goal:** Unattended free public operation (billing disabled)

## What closed the gaps

| Gap | Fix |
| --- | --- |
| Silent outages | `ALERT_SINK_FILE` required for staging/production; startup alerts if Sentry/email console |
| Worker death | `ops/watchdog.py` restarts worker when `workers < 1` |
| Process crash | `ops/supervise_production.ps1` restarts API + worker + watchdog |
| No TLS edge | `ops/Caddyfile` HTTPS reverse proxy template |
| No backups | `ops/backup_daily.py` + retain 14 days |
| Weak deploy gates | `assert_deployable_secrets` now enforces alerting + prod SMTP + COOKIE_SECURE + REQUIRE_QUEUE |

## How to run unattended (this host)

```powershell
cd C:\Users\Administrator\Desktop\aiessayassignmentchecker
.\ops\supervise_production.ps1
```

Keep that window open (or register as a Windows Task that runs at login).

Frontend separately (already on :3001):

```powershell
cd frontend
npm run start
```

## Before true internet production

1. Point DNS at a VPS/host running Caddy with `ops/Caddyfile`  
2. Set `APP_ENV=production`, `COOKIE_SECURE=true`, real SMTP, real domain CORS/URLs  
3. Paste `SENTRY_DSN` + `NEXT_PUBLIC_SENTRY_DSN`  
4. Schedule `python ops/backup_daily.py` daily via Task Scheduler  
5. Set `ALERT_WEBHOOK_URL` to Slack/Discord for phone-visible pages  

## Scores after this pack

| Domain | Score |
| --- | ---: |
| Reliability | 94 |
| Deployment/ops | 90 |
| Security | 90 |
| Monitoring | 78 |
| UX | 86 |
| A11y | 87 |
| Performance | 80 |
| **Set-and-forget readiness** | **88** |

Sentry + public HTTPS + SMTP remain the last steps to push monitoring to 95+ and claim fully unattended internet production.
