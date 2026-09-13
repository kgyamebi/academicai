# Storage Scalability Certification — AcademicCheck AI

Date: 2026-09-09  
Backend measured: **local disk**. S3/R2 adapter in `storage.py` (SSE-AES256, signed URL helper, 5s/15s timeouts, circuit). **Object-store drills not run.**  
Artifact: `ops/cert_storage_results.json` 2026-09-07T09:14:54Z. Score **50 / 100**. **FAIL.**

## Benchmarks requested vs run

| Files | Upload | Download | Failure rate | Status |
| ---: | --- | --- | ---: | --- |
| 1,000 × 4 KiB | 193.3 files/s (5.173 s) | read_ok 1000 (16.659 s) | 0.0 | Pass local |
| 10,000 × 4 KiB | 153.2 files/s (65.285 s) | read_ok 10000 (115.746 s) | 0.0 | Pass local |
| 100,000 | — | — | — | **Not run** |
| 500,000 | — | — | — | **Not run** |
| 1,000,000 | — | — | — | **Not run** |
| S3 / R2 / signed URL load | — | — | — | **Not run** |

## Requested implementations

| Item | Status |
| --- | --- |
| Signed URLs | Code path `signed_url()`; requires S3 keys; **unrun** |
| CDN readiness | **None** for tenant bytes (API `Cache-Control: no-store`) |
| Lifecycle management | Design only — no bucket lifecycle JSON applied |
| Storage optimization | Local 4 KiB files only; reports/PDFs not stored as scaled objects in this drill |

## Verdict

**PASS** 10k local 4 KiB round-trip, 0% read fail.  
**FAIL** 100k–1M files, S3/R2, CDN, lifecycle. Local disk is a scale SPOF.
