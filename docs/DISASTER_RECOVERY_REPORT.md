# Disaster Recovery Report — AcademicCheck AI

Date: 2026-09-07  
Runbook: `docs/RECOVERY_RUNBOOK.md`  
Drill: `docs/DISASTER_RECOVERY_DRILL_REPORT.md`  
Artifact: `ops/cert_restore_audit.json`

## Procedures (exist)

1. Backup: `ops/backup_postgres.sh` (`pg_dump`).
2. Restore: `ops/restore_postgres.sh` (`pg_restore`).
3. Validate: `ops/validate_restore.py` (counts).
4. PITR design: `ops/PITR.md` — **not executed**.

## Restore drills performed (local Docker Postgres 16, port 55432)

| Cycle | restore_s | Outcome |
| --- | ---: | --- |
| Initial | 26.025 | counts match |
| After accidental delete | 24.432 | assignments restored 99755 → 100005 |
| After drop findings | 28.837 | findings 1003300 restored |
| After failed migration | 20.007 | error captured; restore recovered |
| After destroy env | 21.317 | fingerprints match |

RTO (this host): **21.317 s** (fastest restore_s used as reported RTO in the audit file).  
RPO: **point-in-time of last pg_dump only**.  
`managed_postgres`: **false**.

## Full-system recovery

API + Redis + workers + object storage + secrets + DNS **were not** restored as a unit. Redis AOF exists on cert compose; **Redis restore drill not separately signed**. Local disk storage restore **not signed**.

## Verdict

**Local Postgres dump/restore: PASS.**  
**Managed PITR / full-system DR: FAIL.** Do not treat 21 s RTO as a cloud SLA.
