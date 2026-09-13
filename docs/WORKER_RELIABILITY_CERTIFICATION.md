# Worker Reliability Certification

Date: 2026-09-07  
Artifact: `ops/cert_worker_death.json`

## Steady load

5 workers completed 1,000 analysis jobs with 0 stuck (`ops/cert_queue_results.json`).

## Worker death

12 analysis jobs enqueued. Worker process killed after ~3 s. Replacement worker started.

| Result | Count |
| --- | ---: |
| completed | 11 |
| queued (stuck for 120 s) | **1** |
| failed | 0 |

`pass: false`. RQ/SimpleWorker did not recover the orphaned queued row within two minutes. The 900 s stale-job reaper was not waited out.

## Verdict

**FAIL** worker-death zero-stuck. Do not claim exactly-once under process kill.
