# Offsite backup and CRR — AcademicCheck AI

Date: 2026-09-09

## Local emulator (proven)

| Item | Value |
| --- | --- |
| Compose | `ops/docker-compose.minio.yml` (127.0.0.1:59000) |
| Cycle | upload → download → sha256 match → prune |
| Artifact | `ops/cert_offsite_minio.json` |
| Runs | **2/2 PASS**, integrity_ok true both; 80-day key pruned |
| Object | Host `pg_dump` custom (32,893,333 bytes) |

Retention: last **7** calendar days of dumps plus newest object per ISO week for **4** weeks (`ops/offsite_backup.py` `keys_to_delete`). Pytest `tests/test_dr_offsite.py`.

Schedule (code-ready):

- GitHub Actions `.github/workflows/backup-postgres.yml` cron `0 2 * * *` — fail-closed without secrets; with secrets runs `pg_dump` + `offsite_backup.upload_file` + prune.
- systemd `ops/systemd/academiccheck-backup.timer` — install on a bastion when `.env.backup` exists.

To go live: set `BACKUP_DATABASE_URL`, `BACKUP_UPLOAD_URI=s3://bucket/prefix`, `BACKUP_S3_ACCESS_KEY`, `BACKUP_S3_SECRET_KEY`, optional `BACKUP_S3_ENDPOINT` (MinIO/R2 compatible). **No code change required.**

## Cross-region replication (not executed)

Config-as-code: `ops/s3_crr_replication.json`  
Validator: `ops/validate_crr_config.py` → `ops/cert_crr_config.json`

| Field | Status |
| --- | --- |
| syntax_ok | true |
| VersioningRequired | true |
| Prefix `backups/` | specified |
| replication_succeeded | **false** — needs two real regional buckets + IAM role |

MinIO cannot prove AWS CRR. Do not treat emulator PASS as multi-region replication.
