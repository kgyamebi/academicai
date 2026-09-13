# Database Recovery Certification — AcademicCheck AI

Date: 2026-09-09 (second drill, FK relationship checks added)  
Gate for **production**: managed Postgres + PITR + scheduled encrypted offsite dump. **FAIL.**

Local Docker logical recovery: **PASS**.

## Evidence (this drill)

| Artifact | Result |
| --- | --- |
| `ops/cert_restore_audit.json` | `pass: true`, `measured_at: 2026-09-09T20:22:38Z` |
| Provider | `docker-local`, `managed_postgres: false` |
| RTO (destroy env restore) | **27.446 s** |
| RPO | Last `pg_dump` only — WAL PITR **not** exercised |
| `relationships_ok` | **true** (7 FK orphan queries = 0) |

### Simulations

| Simulation | restore_s | Outcome |
| --- | ---: | --- |
| Initial restore | 29.450 | counts match |
| DELETE 250 assignments | 30.069 | 99756 → 100006 |
| DROP `analysis_findings` | 27.542 | 1003333 restored |
| Failed migration | 27.146 | recovered |
| destroy env | 27.446 | counts + fingerprints + **FK orphans 0** |

Tables restored: users 7, assignments 100006, documents 7 (rows only), reports 1112, findings 1003333, jobs 3113, payments/credits/subscriptions 1 each.

Fingerprints remain COUNT\|MIN(id)\|MAX(id) — **not** full-row hashes (DR-11 residual). Relationship checks close *orphan FKs*, not in-place value corruption.

## Verdict

| Claim | Result |
| --- | --- |
| Local logical backup → scratch restore → counts/fingerprints/FK orphans | **PASS** |
| Automated production backups / PITR | **FAIL** |
| Production database recovery certified | **FAIL** |
