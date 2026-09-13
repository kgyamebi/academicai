# Storage Recovery Certification — AcademicCheck AI

Date: 2026-09-09  

## Local-disk recovery — PASS (this pass)

Script: `ops/verify_storage.py`  
Artifact: `ops/cert_storage_recovery.json`

| Step | Result |
| --- | --- |
| Seed essay/PDF/txt fixtures | ok |
| Backup tree + per-file SHA-256 sidecars | ok |
| Delete one file + corrupt another | ok |
| Restore from backup | ok |
| Verify inventory hashes match baseline | ok |

`s3_replication: false`. `versioning: drill-sidecar-sha256` (drill tooling, not bucket versioning).

## S3 / R2 / Azure — FAIL unrun

| Capability | Status |
| --- | --- |
| Bucket versioning | Not evidenced |
| Cross-region replication | Not evidenced |
| Object-lock | Not evidenced |
| Restore after bucket loss | Not evidenced |
| Chaos `storage_kill` | Not run (`ops/cert_chaos_results.json`) |

## Coupling

Postgres restore recovers `documents` **rows** only. Upload bytes are a separate recovery domain (DR-04). Combined DB+object drill: **unrun**.

## Verdict

**PASS** local checksummed backup/restore drill.  
**FAIL** object-storage / multi-region recovery certification.
