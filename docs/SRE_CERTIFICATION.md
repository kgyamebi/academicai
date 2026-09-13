# SRE Certification Report

Date: 2026-09-07  
Gate: production operations ready. **Fail.**

## What exists in-repo

| Item | Location | Exercised this pass? |
| --- | --- | --- |
| Recovery runbook | `docs/RECOVERY_RUNBOOK.md` | Restore drill yes (local Docker) |
| Alerts / SLOs (specified) | `docs/ALERTS_AND_SLOS.md` | Not wired to a pager |
| Backup script | `ops/backup_postgres.sh`, `ops/cert_restore.py` | Dump+restore yes |
| Health | `/api/live`, `/api/ready` | Chaos yes |
| Queue ops | `REQUIRE_QUEUE`, DLQ | 1000 jobs yes |
| Secret rotation notes | existing rotate docs | Not drilled |

## Missing for SRE certification

- On-call roster and escalation matrix **as a staffed function** (a markdown list is not a roster)
- PagerDuty / Opsgenie (or equivalent) firing from production metrics
- Disaster recovery RTO/RPO measured on the **managed** database, not Docker volumes
- Blue-green / canary rollback rehearsal
- Game day covering AI and billing providers

Incident response for Redis/Postgres down is: live stays 200, ready 503 (measured). That is not a full IR program.

## Verdict

**Not SRE-certified for paid production.** Local restore + chaos are necessary but not sufficient.
