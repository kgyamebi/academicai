# Disaster Recovery Certification — AcademicCheck AI

Date: 2026-09-09  
Local engineerable package: **PASS** (`ops/cert_dr_repeat.json` `ok_local_package: true`).  
Production DR: **FAIL**. Launch: **NO-GO**.

Evidence-backed DR score: **86 / 98** (was 82). Raised only for host-export restore, local WAL PITR, MinIO offsite cycle, queue SIGKILL+AOF, and app-level storage restore — each with **two consecutive** runs. Not a managed-PITR or live-S3 certificate.

## Scorecard

| Drill | Result | Artifact | Repeats |
| --- | --- | --- | --- |
| Host dump export (sha256, in-container copy deleted) | **PASS** | `ops/cert_backup_host_export.json` | 1 export (source of restore) |
| Destroy isolated DB → restore from **host copy only** | **PASS** counts match 1,003,333 findings | `ops/cert_host_restore.json` | **2/2**, RTO 43.346 / 43.067 s |
| MinIO upload/download/integrity/prune | **PASS** | `ops/cert_offsite_minio.json` | **2/2** |
| Local WAL PITR (timestamp between two writes) | **PASS** (keep A, drop B) | `ops/cert_wal_pitr.json` | **2/2** |
| Storage destroy → restore → `read_bytes` | **PASS** | `ops/cert_storage_app_restore.json` | **2/2** |
| Redis `docker kill` queued jobs | **PASS** 12/12 both runs | `ops/cert_queue_crash.json` | **2/2** |
| S3 CRR | Syntax **PASS**, apply **FAIL unrun** | `ops/cert_crr_config.json` | n/a |
| Managed provider PITR | **FAIL** pending live account | — | — |
| Real bucket GHA schedule | **FAIL** secrets unset | `.github/workflows/backup-postgres.yml` | — |
| Multi-region failover | **FAIL** unrun | `docs/MULTI_REGION_DR_PLAN.md` | — |
| Human prod dump/restore | **AWAITING HUMAN** | `docs/PROD_DR_DRILL.md` | — |
| Worker SIGKILL stuck job | **FAIL** historical | `ops/cert_worker_death.json` | — |

## RTO consistency (local)

Host restore: 43.346 s vs 43.067 s (`rto_consistent: true`).  
WAL PITR both runs excluded the post-target row.

## APPROVED FOR LAUNCH (DR): NO
