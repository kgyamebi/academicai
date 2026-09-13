# LAUNCH_CERTIFICATION

**Product:** AcademicCheck AI (billing disabled)  
**Measured:** 2026-09-13T21:27:00Z  

## Verdict

# **SET-AND-FORGET READY (local/staging) — 88/100**

Internet “production” still needs: HTTPS edge + SMTP + Sentry DSN.

## Scores

| Domain | Score |
| --- | ---: |
| Reliability | 94 |
| Deployment / supervision | 90 |
| Security | 90 |
| Monitoring / alerting | 78 |
| UX | 86 |
| Accessibility | 87 |
| Performance | 80 |
| **Set-and-forget** | **88** |

## Closed this pass

- Watchdog (`ops/watchdog.py`) + auto worker restart  
- Process supervisor (`ops/supervise_production.ps1`)  
- Mandatory alert sink/webhook for staging/production  
- Startup alerts for missing Sentry / console email  
- Caddy HTTPS template (`ops/Caddyfile`)  
- Daily backup script (`ops/backup_daily.py`)  
- Stricter deploy gates (prod: COOKIE_SECURE, SMTP, REQUIRE_QUEUE)

## Still on you (credentials / DNS)

1. `SENTRY_DSN` + browser DSN  
2. Real SMTP  
3. Domain + Caddy (or Cloudflare) HTTPS  
4. `ALERT_WEBHOOK_URL` for Slack/Discord phone alerts  
5. Schedule `backup_daily.py` in Task Scheduler  

See `docs/reports/SET_AND_FORGET_PRODUCTION.md`.
