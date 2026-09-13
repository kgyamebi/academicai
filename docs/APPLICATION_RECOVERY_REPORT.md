# Application Recovery Report — AcademicCheck AI

Date: 2026-09-09  

## Failure modes

| Failure | Recovery path | Proven? |
| --- | --- | --- |
| API process crash | Compose `restart: unless-stopped` + `/api/ready` | Local chaos historical |
| Bad deploy | `ops/rollback_compose.sh` / prior image | Script exists; prod CD unproven |
| Worker failure | RQ retry + DLQ + `recover_jobs.py` | Partial (see queue cert) |
| Config / secret loss | `ops/rotate-secrets.md` + secret manager (HAL-08) | Manager **UNPROVEN** |
| Env destruction (DB) | Scratch restore | **PASS** local 2026-09-09 |

## Blue-green

`ops/cert_bluegreen.py` / `ops/cert_bluegreen_results.json` — local proxy drill only. Not a multi-region cutover.

## Verdict

**PARTIAL** — local compose restart/rollback tooling + DB restore. **FAIL** production release recovery / secret recovery certification.
