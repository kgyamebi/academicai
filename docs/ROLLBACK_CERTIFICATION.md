# Rollback Certification

Date: 2026-09-07  
Local drill: `ops/cert_bluegreen.py` health watcher flips `active` from green to blue when green `/api/live` fails.

GitHub: `.github/workflows/deploy-rollback-drill.yml` **exits 1** unless `STAGING_URL` secret is set. That workflow was **not** executed on GitHub in this pass.

| Trigger | Automatic rollback proven? |
| --- | --- |
| Broken process (green killed) | Yes, local proxy |
| Failed health checks | Yes, local `/api/live` |
| Migration error | **No** |
| Performance regression | **No** |
| Cloud CD | **No** |

Go-live “Automatic Rollback = PASS” for production pipeline: **FAIL**.
