# Queue Scalability Certification — AcademicCheck AI

Date: 2026-09-09  
Broker: Redis + **RQ** (not Celery).  
Gate: 25k/50k **analysis** jobs with 0 lost/dup/stuck. **FAIL.**  
No new analysis-job volume was run this pass. Numbers below are still `ops/cert_queue_results.json` (2026-09-07T09:20:04Z) and ping artifacts.

## Audit

| Control | Status | Evidence |
| --- | --- | --- |
| Redis pool | `max_connections=64`, timeout 2s | `queue.py` |
| Dedup | `job_id` + `DuplicateJobError` | code + pytest |
| Retry | RQ Retry 3× with jitter | `queue.py` `_retry_intervals_with_jitter` |
| DLQ | `record_poison_job` | code |
| Backpressure | enqueue false / 503 if no Redis or `REQUIRE_QUEUE` | chaos + pytest |
| Depth metric | `academiccheck_queue_depth` | prometheus text |
| Recovery | 1 stuck after SIGKILL | `cert_worker_death.json` |

## Requested analysis volumes

| Jobs | Kind | Lost | Dup | Stuck | Throughput / min | Result |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 1,000 | **analysis** | 0 | 0 | 0 | 209.2 (5 workers, 286.8 s) | **PASS** |
| 5,000 | **ping** not analysis | 0 | — | 0 queued | 3439.5 | PASS ping only |
| 10,000 | **ping** | 0 | — | 0 queued | 3691.6 | PASS ping only |
| 25,000 | — | — | — | — | — | **Not run** |
| 50,000 | — | — | — | — | — | **Not run** |

Queue lag: depth gauge only, no age histogram. Duplicate rate on analysis 1000-job run: **0**. Lost job rate: **0**. Worker utilization: 5 workers started; host CPU **not sampled**.

## Verdict

**Certified: 1,000 analysis jobs, 0/0/0.**  
**Not certified: 5k–50k analysis jobs.** Ping throughput is not analysis capacity. Orphan/stuck residual remains after worker SIGKILL.
