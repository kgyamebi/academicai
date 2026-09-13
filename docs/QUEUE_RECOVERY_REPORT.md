# Queue Recovery Report — AcademicCheck AI

Date: 2026-09-07  
Broker: **Redis + RQ** (`python -m app.workers.rq_worker`). Not Celery.  
DR score unchanged. This is not a zero-loss certificate.

## Audit

| Component | Persistence | Recovery evidence |
| --- | --- | --- |
| Redis | AOF on cert/prod compose (`appendonly yes`) | Process stop: ready 503 then 200 (`ops/cert_chaos_results.json` 2026-09-07T12:36:39Z). **AOF file restore not signed** (DR-09) |
| RQ `analysis` queue | Jobs in Redis; status in Postgres | 1000 jobs (`ops/cert_queue_results.json`) |
| Workers | Stateless processes | Kill: `ops/cert_worker_death.json` |

Controls in code (not a substitute for drills): DLQ `record_poison_job`, Retry 3×, `job_timeout=600`, stable `job_id` / `DuplicateJobError`, `reap_stale_jobs` 900s, fail-closed enqueue. Pytest: `backend/tests/test_queue_recovery.py`, `test_reliability_failures.py`.

## Recovery scenarios

| Scenario | Result | Evidence | Lost | Orphan/stuck | Duplicate |
| --- | --- | ---: | ---: | ---: | ---: |
| Happy path 1000 analysis jobs, 5 workers | **PASS** | `cert_queue_results.json` 2026-09-07T09:20:04Z | 0 | 0 | 0 |
| Ping 5000 / 10000 | **PASS** (ping, not analysis) | `cert_queue_ping_*.json` | 0 | — | — |
| Ping 50000 | **not completed** | listed `not_run` on 1000-job artifact | — | — | — |
| Worker death (SIGKILL-style) | **FAIL** | `cert_worker_death.json` 11 completed, **queued stuck=1**, `pass: false` | 0 claimed lost | **1 stuck** | not reported |
| Redis process outage | **PASS** (health) | chaos: live 200, ready 503, recover 200 | jobs in Redis **not counted** during outage | unknown | unknown |
| Redis restart / queue interruption | same chaos | recover ready 200 | **not** a job-inventory audit | unknown | unknown |
| Job interruption mid-process | reaper 900s / retry | pytest + death drill | death drill incomplete | **1** | enqueue dedup in code, death drill didn’t measure dup |

## Verdicts requested by the mission

| Requirement | Proven? |
| --- | --- |
| No lost jobs | **Yes** at 1000 analysis jobs. **Not** proven at worker kill (stuck ≠ lost, but not completed). **Not** proven across Redis volume loss |
| No orphaned jobs | **No** — 1 queued stuck after kill |
| No stuck jobs | **No** — same |
| No duplicate jobs | **Yes** at 1000 (`duplicate_ids: 0`). Code has `DuplicateJobError`. Kill drill did not re-measure dups |

**Queue recovery is not certified** for production. Reliable at 1k analysis jobs on that workstation. Fail closed when Redis is down (`enqueue_analysis` false / ready 503).
