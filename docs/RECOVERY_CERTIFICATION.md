# Recovery Certification

Date: 2026-09-07  
Gate: managed Postgres restore + PITR. **FAIL.**

Evidence: `ops/cert_restore_audit.json`, `docs/RESTORE_AUDIT.md`.

| Requirement | Result |
| --- | --- |
| Backup | `pg_dump --format=custom` inside Docker |
| Restore | Five successful `pg_restore` cycles |
| Validation | Row counts + min/max id fingerprints |
| Destroy test env + restore again | Pass |
| Table drop / accidental delete / failed migration | Pass after restore |
| Users, assignments, documents, reports, findings, credits, payments, subscriptions | Counts restored |
| Managed provider | **false** |
| WAL PITR | **not run** |

Do not treat Docker volume backup as a multi-AZ managed recovery certificate.
