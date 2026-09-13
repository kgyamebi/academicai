# Disaster Recovery Plan — AcademicCheck AI

Date: 2026-09-07  
Risks: `docs/DISASTER_RECOVERY_RISK_REGISTER.md`  
Objectives: `docs/RECOVERY_OBJECTIVES.md`  
BCP: `docs/BUSINESS_CONTINUITY_PLAN.md`  
Runbook: `docs/RECOVERY_RUNBOOK.md`  
Evidence: `docs/DISASTER_RECOVERY_REPORT.md`, `docs/DATABASE_RECOVERY_CERTIFICATION.md`, `ops/cert_restore_audit.json`

## Objectives (design, not certified)

- RPO: 5 minutes **if** managed PostgreSQL PITR is enabled.
- RTO: 60 minutes for a staging restore drill.

Measured locally (Docker Postgres 16, `pg_dump`/`pg_restore` only): RTO **21.317 s**, RPO = last dump, `managed_postgres: false`.

## Backup

1. `bash ops/backup_postgres.sh` (plaintext dump — **not** encrypted-at-rest backup).
2. Keep dump off the API host.
3. Enable provider PITR (`ops/PITR.md`) — **not executed**.

## Restore

1. Snapshot counts: assignments, documents, analysis_reports, credits, payments, subscriptions, analysis_jobs, findings.
2. Restore with `bash ops/restore_postgres.sh`.
3. `python ops/validate_restore.py` — **counts only**. Id fingerprints are from `ops/cert_restore_audit.py`, not this script.
4. Login as a test tenant; open assignment, document, report, billing. File bytes are **not** in the dump.

## What this plan does not cover

Redis AOF restore, object-storage restore, secret rotation as a unit, DNS, and multi-region failover were **not** drilled.

## Certification

**Local dump/restore: PASS.** **Managed PITR / full-system DR: FAIL.**
