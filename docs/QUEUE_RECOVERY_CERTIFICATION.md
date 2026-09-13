# Queue Recovery Certification — AcademicCheck AI

Date: 2026-09-09  

## Protections implemented

| Control | Location | Proven? |
| --- | --- | --- |
| RQ Retry (3×) | `enqueue_analysis` | Code + queue cert historical |
| Dead letter `analysis_dlq` | `queue.py` `_on_failure` | pytest `test_on_failure_enqueues_dead_letter` |
| Job idempotency (`job_id`) | RQ `DuplicateJobError` / fetch existing | Code |
| Orphan heartbeat recovery (exactly once) | `recover_orphaned_jobs` | pytest + `ops/recover_jobs.py` |
| Stale reaper | `reap_stale_jobs` (900s) | Code / worker path |
| Dedup terminal jobs | `_job_already_terminal` | Code |

## Tests

| Test | Result |
| --- | --- |
| Orphan recover then fail on second crash | **PASS** `test_recover_orphaned_job_exactly_once` |
| Historical 1000 analysis jobs | **PASS** `ops/cert_queue_results.json` (prior) |
| Worker SIGKILL 12/12 zero stuck | **FAIL** historical `cert_worker_death.json` `pass: false` |
| Queue corruption / Redis wipe + full replay | **UNPROVEN** |

## Operator recovery

```text
DATABASE_URL=... python ops/recover_jobs.py --out ops/cert_job_recovery.json
```

## Verdict

**PARTIAL PASS** — DLQ + orphan recovery certified in pytest; load cert historical.  
**FAIL** zero-stuck worker-kill and Redis-wipe queue reconstruction.
