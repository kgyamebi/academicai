# Backup Architecture — AcademicCheck AI

Date: 2026-09-09  
Local logical dump + host export + MinIO offsite cycle: **PASS** (repeated).  
Production automated offsite to a live cloud account + managed PITR: **FAIL / AWAITING LIVE ACCOUNT**.

## Components

| Layer | Mechanism | Evidence |
| --- | --- | --- |
| Full logical dump | `pg_dump` custom | Host export `ops/cert_backup_host_export.json` (32,893,333 bytes, sha256 `0cbb3455…`) |
| Host copy (container-independent) | `ops/export_backup_host.py` `docker cp` → `backups/host/*.dump` + `.sha256`; in-container copy deleted | Same artifact `in_container_copy_deleted: true` |
| Isolated restore from host only | Empty Postgres on `:55433`, `down -v` between runs | `ops/cert_host_restore.json` **2/2 PASS**, RTO 43.346 s / 43.067 s, 1,003,333 findings |
| Encrypted at rest (dump file) | AES-256-GCM (`ops/backup_crypto.py`) | Prior `cert_dr_local_drill.json` round-trip |
| Offsite (emulator) | MinIO S3 API upload/download/sha256 + retention prune | `ops/cert_offsite_minio.json` **2/2 PASS** |
| Offsite (live) | GHA `backup-postgres.yml` 02:00 UTC + `ops/offsite_backup.py` | **Ready, pending secrets** |
| Schedule (local OS) | `ops/systemd/academiccheck-backup.timer` daily 02:00 UTC | Unit files present; not installed on this workstation |
| WAL / PITR (engine) | `ops/docker-compose.pitr.yml` + `ops/cert_wal_pitr.py` | `ops/cert_wal_pitr.json` **2/2 PASS** (row A kept, row B excluded) |
| Managed PITR | RDS/Neon/Cloud SQL | **Pending live account** |
| CRR | `ops/s3_crr_replication.json` | Syntax PASS; `replication_succeeded: false` |
| Object storage bytes | App `store_bytes` / `read_bytes` | `ops/cert_storage_app_restore.json` **2/2 PASS** |

## Operator flow (local cert)

1. `py -3.14 ops/export_backup_host.py`
2. Confirm `backups/host/academiccheck-*.dump` and sidecar sha256.
3. `py -3.14 ops/cert_host_restore.py` — uses **only** the host file; destroys the isolated volume after each run.
4. Optional encrypt: `BACKUP_ENCRYPTION_KEY=…` + `ops/backup_crypto.py`.
5. Offsite emulator: `docker compose -f ops/docker-compose.minio.yml up -d` then `py -3.14 ops/cert_offsite_minio.py`.

## Gaps that remain live-account / human

- GHA dump/upload against real `BACKUP_DATABASE_URL` + bucket.
- S3 CRR apply in two regions.
- Managed provider PITR drill.
- Human production dump into isolated restore (`docs/PROD_DR_DRILL.md`).
