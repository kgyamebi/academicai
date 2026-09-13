# Remaining Recovery Risks — AcademicCheck AI

Date: 2026-09-09

## Closed this pass (local evidence)

| ID | Was | Now | Evidence |
| --- | --- | --- | --- |
| DR-02 | WAL replay unrun | **Local WAL PITR PASS** (2/2) | `ops/cert_wal_pitr.json` |
| DR-03 (local) | Offsite unproven | **MinIO cycle PASS** (2/2) | `ops/cert_offsite_minio.json` |
| Host-only dump | In-container only | **Host export + isolated restore 2/2** | `ops/cert_backup_host_export.json`, `ops/cert_host_restore.json` |
| DR-04 (local disk) | Object restore fixture only | **App `read_bytes` after restore 2/2** | `ops/cert_storage_app_restore.json` |
| DR-09 (volume retained) | Restart only | **docker kill, 12/12 jobs both runs** | `ops/cert_queue_crash.json` |

## Still blocked on a live cloud account or human prod credentials

| ID | Severity | Risk | Why it cannot close here |
| --- | --- | --- | --- |
| DR-01 | Critical | Managed PITR feature | Vendor console / PITR API; local WAL is the engine, not the product |
| DR-03 (prod) | Critical | Scheduled dump to a real bucket | GHA secrets unset by design |
| DR-05 | Critical | S3/R2 restore of customer objects | No live bucket |
| DR-05b | Critical | S3 CRR | Config valid; apply unrun (`replication_succeeded: false`) |
| DR-06 | Critical | Live PSP recovery | No PSP keys |
| DR-07 | Critical | Secret manager restore | No manager |
| DR-08 | Critical | Combined full-system prod drill | Needs prod |
| DR-09b | High | Redis **volume-loss** (`down -v`) | Kill+AOF with volume retained is proven; empty-volume rebuild is not |
| DR-10 | High | Worker SIGKILL stuck job | Historical `cert_worker_death.json` stuck=1 |
| DR-11 | High | Fingerprints COUNT\|MIN\|MAX | Unchanged |
| DR-12 | High | Dual dump formats | Cert/host = custom; `backup_postgres.sh` = gzip SQL |
| DR-14 | High | Multi-region failover | Plan complete; no second region |
| DR-15 | High | CI restore of prod-sized dump | CI still sqlite |
| Human prod dump | Critical | `docs/PROD_DR_DRILL.md` | AWAITING HUMAN |

Production DR remains **NO-GO**. Local package: `ops/cert_dr_repeat.json` `ok_local_package: true`.
