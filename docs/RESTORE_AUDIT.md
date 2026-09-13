# Restore Audit

Date: 2026-09-07  
Provider: **Docker Postgres 16 on localhost:55432** (`managed_postgres: false`)  
Artifact: `ops/cert_restore_audit.json`

This is **not** Amazon RDS, Cloud SQL, Neon, or any vendor-managed instance. WAL PITR was not replayed.

## RTO / RPO

| Target | Measured |
| --- | --- |
| RTO (destroy restore DB → `pg_restore`) | **21.317 s** |
| RPO | Last `pg_dump` only (dump 11.131 s). Continuous WAL restore **not exercised**. |

## Integrity

Fingerprints: `sha256(count\|min(id)\|max(id))` per table, 16-hex prefix. `fingerprints_match: true` after delete/drop/failed-migration restores.

| Table | Rows |
| --- | ---: |
| users | 6 |
| assignments | 100,005 |
| documents | 6 |
| analysis_reports | 1,101 |
| analysis_jobs | 3,101 |
| analysis_findings | 1,003,300 |
| payments | 1 |
| credits | 1 |
| subscriptions | 1 |

## Scenarios

| Scenario | What happened | Restore | Counts match dump |
| --- | --- | ---: | --- |
| Initial restore to `academiccheck_restore` | `pg_restore` | 26.025 s | Yes |
| Accidental DELETE 250 assignments | Count fell to 99,755 | 24.432 s | Yes (100,005) |
| DROP TABLE analysis_findings | Table gone | 28.837 s | Yes (1,003,300) |
| Failed migration (`NOT NULL` column, no default) | `psql` error captured | 20.007 s | Yes |
| Destroy restore environment (`dropdb --force`) | Empty | 21.317 s | Yes |

## Verdict

**PASS** for local logical dump/restore integrity.  
**FAIL** for go-live item “Managed PostgreSQL backup/restore”.
