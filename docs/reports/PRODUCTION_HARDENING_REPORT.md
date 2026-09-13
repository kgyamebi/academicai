# PRODUCTION_HARDENING_REPORT

**Measured:** 2026-09-13T21:20:27Z  

| Control | Status |
| --- | --- |
| Staging compose | Present (`docker-compose.staging.yml`) |
| APP_DEBUG=false in staging | Yes (compose) |
| Secrets in repo | Staging placeholders only |
| Redis AOF | Enabled in staging compose |
| Backup/restore | See `docs/LAUNCH_RECOVERY_RUNBOOK.md` |
| Rollback | `ops/rollback_compose.sh` |
| Worker restart | `restart: unless-stopped` |

Docker Desktop must be running to apply compose on this host.
