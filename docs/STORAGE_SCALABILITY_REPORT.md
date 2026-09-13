# Storage Scalability Report

Date: 2026-09-07  
Unchanged measurement: `ops/cert_storage_results.json`

| Drill | Result |
| --- | --- |
| 10,000 × 4 KiB local files | 0% read fail |
| 100k / 1M files | **not run** |
| S3/R2 signed URL throughput | **not run** |
| Concurrent download SLO | **not run** |

Path traversal is rejected in validation. Lifecycle/cleanup/monitoring for object storage are design-only (`docs/STORAGE_SCALABILITY.md`).

**Score: 50 / 100.** Do not certify object-storage scale.
