# Reliability Certification Report

**Product:** AcademicCheck AI (public free launch · billing disabled)  
**Date:** 2026-09-13  
**Evidence pack:** `ops/evidence/free_launch_verification_2026-09-13.json`  
**Gate:** 98+ with staging proof  

## Verdict

| Metric | Score | Gate |
| --- | ---: | --- |
| Evidence-backed reliability | **86 / 100** | **98 FAIL** |

**Certification: NOT ISSUED.** Staging environment not available (`STAGING_URL=absent`).

## Measured this pass

| Check | Result | Evidence |
| --- | --- | --- |
| Local `GET /api/live` | 200; n=20 avg **25.85 ms** | evidence JSON probes |
| Local `GET /api/ready` | 200 but `redis=false`, `workers=null`, still `ready=true` (`env=development`) | evidence JSON |
| Sequential `/api/live` ×50 | **49/50** HTTP 200; avg **493.3 ms** | evidence JSON |
| Chaos fail-closed (lab) | live stays 200; ready 503 when Redis/Postgres down; recover 200 | `ops/cert_chaos_results.json` (2026-09-07) |
| Queue 1000 jobs (lab) | 1000 completed, lost=0, dup=0, stuck=0 | `ops/cert_queue_results.json` |
| Restore row-count (lab Docker) | counts_match=true | `ops/cert_restore_results.json` |
| Reliability pytest pack | **59 passed** after fixing billing-circuit test signature drift | pytest log 2026-09-13 |

## Open High / Critical (blocks 98)

| ID | Severity | Finding | Required proof |
| --- | --- | --- | --- |
| REL-S1 | **High** | No staging URL; host recovery unproven | `STAGING_URL` + `/api/ready` with redis+workers ≥1 |
| REL-S2 | **High** | Local ready green without Redis/workers (dev policy) | Staging `REQUIRE_QUEUE=true` ready=200 only with workers |
| REL-S3 | **High** | Managed PITR / offsite restore not attested on host | Signed restore artifact on staging DB |
| REL-S4 | Medium | 1/50 live miss under light sequential load locally | Re-measure on staging; error budget |
| REL-S5 | Medium | Multi-day uptime not attested | ≥7d uptime window or synthetic monitor |

## Path to 98 (measurable)

1. Deploy staging; set `STAGING_URL`.  
2. Prove `curl -sf $STAGING_URL/api/ready` → `database=true redis=true workers>=1`.  
3. Re-run `ops/cert_chaos.py` and `ops/cert_queue.py` against staging Redis/Postgres.  
4. Execute `docs/FAILURE_RECOVERY_CHECKLIST.md`; attach timestamps.  
5. Wire `ALERT_WEBHOOK_URL`; fire ready=503 drill (`ops/cert_alert_fire.py`).  
6. Zero Critical/High remaining → re-score.

## Sign-off

Reliability 98+: **NO**  
Signed: _pending staging evidence_
