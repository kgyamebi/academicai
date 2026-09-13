# Queue Certification Report

Date: 2026-09-07  
Redis: Docker Redis 7 AOF `127.0.0.1:56379`  
Workers: 5 × `SimpleWorker` (Windows)

## Analysis jobs (`run_analysis_job`)

| Jobs | Completed | Lost | Dup | Stuck | Failed | Artifact |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1,000 | 1,000 | 0 | 0 | 0 | 0 | `ops/cert_queue_results.json` |
| 5,000 analysis | — | — | — | — | — | **Not run** |
| 10,000 analysis | — | — | — | — | — | **Not run** |
| 50,000 analysis | — | — | — | — | — | **Not run** |

## RQ ping volume (`cert_ping` no-op)

Certifies Redis/RQ enqueue+complete, **not** full analysis persist.

| Jobs | Completed | Failed | Lost | Queued left | Throughput / min | Artifact |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 5,000 | 5,000 | 0 | 0 | 0 | 3,439.5 | `ops/cert_queue_ping_5000.json` |
| 10,000 | 10,000 | 0 | 0 | 0 | 3,691.6 | `ops/cert_queue_ping_10000.json` |
| 50,000 | — | — | — | — | — | **Not completed** (run hung on finished-registry TTL; not re-proven after kill) |

Dedup: stable `job_id` + `DuplicateJobError` in `enqueue_analysis`. Ping re-enqueue after completion is allowed (job gone).

## Verdict

**PASS** at 1,000 real analysis jobs and 10,000 ping jobs with zero loss/fail.  
**FAIL** go-live if 50,000 jobs or 5,000 **analysis** jobs are mandatory. Worker-kill drill left **1/12** analysis jobs queued (`ops/cert_worker_death.json`).
