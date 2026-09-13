# Automated Recovery Report — AcademicCheck AI

Date: 2026-09-09  

## Scripts (Phase 13)

| Script | Role | Tested? |
| --- | --- | --- |
| `ops/restore_database.sh` | Guarded entry to gzip restore | Contract test (guards present); full bash restore needs Unix + scratch URL |
| `ops/validate_restore.py` | Tenant table counts | Used in prior drills; fail-closed without URL |
| `ops/reconcile_billing.py` | Alias to billing reconcile + alert | pytest alert path |
| `ops/recover_jobs.py` | Orphan/stale job recovery | Refuses without DB URL (pytest); logic via runner tests |
| `ops/verify_storage.py` | Object tree backup/restore/checksum | **PASS** `cert_storage_recovery.json` |
| `ops/backup_verification.py` | Gzip/decrypt integrity | **PASS** pytest + local drill |
| `ops/backup_crypto.py` / `encrypt_backup_file.py` | AES-GCM dump envelope | **PASS** round-trip |
| `ops/dr_local_drill.py` | Package runner | `cert_dr_local_drill.json` `ok_local_package: true` |
| `ops/cert_restore_audit.py` | Full DB disaster simulations | **PASS** 2026-09-09 |
| `ops/redis_recovery_check.py` | Persistence probe | **PASS** on cert Redis |

## Integrity checks

- Counts + id fingerprints (DB)
- SHA-256 per object (storage drill)
- Gzip stream validity + optional decrypt
- Billing mismatch alert

## Verdict

Automation for **local/cert** recovery is real and evidenced.  
Production scheduled restore validation in CI: **still absent** (sqlite CI).
