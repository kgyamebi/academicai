# Storage Certification Report

Date: 2026-09-07  
Backend tested: **local disk** (`tmp/cert_storage`)  
S3 / Cloudflare R2: **not run**

Artifact: `ops/cert_storage_results.json`

| Files | Size each | Write files/s | Read ok | Failure rate | Status |
| ---: | --- | ---: | ---: | ---: | --- |
| 1,000 | 4 KiB | 193.3 | 1,000 | 0.0 | Pass |
| 10,000 | 4 KiB | 153.2 | 10,000 | 0.0 | Pass |
| 100,000 | — | — | — | — | **Not run** |
| 500,000 | — | — | — | — | **Not run** |
| 1,000,000 | — | — | — | — | **Not run** |

Signed URLs, object deletion at scale, and retention cleanup against R2/S3 were **not** measured.

## Verdict

Local 10k-file round-trip is lossless on this workstation. **Object storage is not certified.**
