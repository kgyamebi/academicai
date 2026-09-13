# Restore Certification Report

Date: 2026-09-07  
Method: `pg_dump --format=custom` inside the cert Postgres container → `createdb academiccheck_restore` → `pg_restore --no-owner`

Artifact: `ops/cert_restore_results.json`  
Script: `ops/cert_restore.py`

## Drill

| Step | Result |
| --- | --- |
| Dump | 18.247 s |
| Restore | 40.218 s |
| Count match (users, assignments, documents, reports, jobs, payments, credits, subscriptions) | **true** |
| Assignments | 100,000 → 100,000 |
| Payments / credits / subscriptions | 1 → 1 |
| Findings on restore database (psql COUNT) | **1,000,000** |

This restore did **not** delete the primary `academiccheck` database. It restored into `academiccheck_restore` and compared counts. Documents on local disk / R2 were not part of the dump. Credits and payments were the cert seed rows, not a production ledger.

`ops/validate_restore.py` prints the same tenant tables; this drill used equivalent SQL counts.

## Verdict

**Pass** for Postgres logical restore of the cert dataset. **Not** a managed PITR / production-account restore.
