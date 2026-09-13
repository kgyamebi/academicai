# Disaster Recovery Runbooks — AcademicCheck AI

Date: 2026-09-09  
Index of operable runbooks. Detailed steps live in `docs/RUNBOOK_LIBRARY/`.

| Disaster | Runbook | Primary scripts |
| --- | --- | --- |
| Database disaster | `RUNBOOK_LIBRARY/database-failure.md`, `restore-failure.md`, `data-corruption.md` | `backup_postgres.sh`, `restore_database.sh`, `validate_restore.py`, `cert_restore_audit.py` |
| Storage disaster | `RUNBOOK_LIBRARY/storage-failure.md` | `verify_storage.py` (+ provider console for S3) |
| Redis disaster | `RUNBOOK_LIBRARY/redis-failure.md` | `redis_recovery_check.py`, compose restart |
| Worker / queue disaster | `RUNBOOK_LIBRARY/worker-failure.md`, `queue-backlog.md` | `recover_jobs.py` |
| Billing disaster | `RUNBOOK_LIBRARY/billing-failure.md`, `payment-webhook-failure.md`, PSP files | `reconcile_billing.py` |
| Security incident | `RUNBOOK_LIBRARY/security-incident.md` | rotate-secrets, session revoke |
| Major outage | `INCIDENT_RESPONSE_PLAN.md` + status/comms in BCP | ready probe, halt paid traffic |
| Region failure | `MULTI_REGION_DR_PLAN.md` (design) | **no automated cutover** |
| Backup failure | `RUNBOOK_LIBRARY/backup-failure.md` | alerting + re-run dump |
| Deployment failure | `RUNBOOK_LIBRARY/deployment-failure.md`, `deployment-rollback.md` | `rollback_compose.sh` |

## Prod DR package (human-gated)

See `docs/PROD_DR_DRILL.md` — backup → isolated restore → verify. **AWAITING HUMAN** against real prod credentials.

## Rule

No runbook is a substitute for a failed drill. Prefer artifacts under `ops/cert_*.json`.
