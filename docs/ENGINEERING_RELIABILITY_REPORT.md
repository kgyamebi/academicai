# Reliability / Worker Report — AcademicCheck AI

Date: 2026-09-07  
Also: `docs/QUEUE_RELIABILITY_REPORT.md`, `docs/CHAOS_ENGINEERING_REPORT.md`.

## Queue controls (code)

| Control | Implementation |
| --- | --- |
| Retry | RQ `Retry(max=3, interval=[15, 60, 180])` |
| Timeout | `job_timeout=600` |
| Dedup | stable `job_id`, `DuplicateJobError`, skip if already queued/started |
| Terminal skip | `_job_already_terminal` (completed/cancelled/failed) |
| DLQ | `analysis_dlq` + `record_poison_job` → `fail_job` |
| Stale reap | `reap_stale_jobs` on job start; GET analysis also reaps |
| Enqueue fail-closed | no workers / Redis error → false; API 503 when required |
| SIGTERM | `rq_worker.py` `request_stop` |
| This pass | log `worker_count_unavailable`, `queue_depth_unavailable`, `terminal_job_lookup_failed` |

## Measured drills (not re-run this pass unless noted)

| Drill | Result | Artifact |
| --- | --- | --- |
| 1000 analysis jobs / 5 workers | 1000 completed, 0 lost, 0 dup, 0 stuck, DLQ 0 | `ops/cert_queue_results.json` 2026-09-07T09:20:04Z |
| Worker SIGKILL-style | 11/12 completed, **1 queued stuck** | `ops/cert_worker_death.json` 2026-09-07T10:52:58Z **FAIL** |
| Redis/PG down | live 200, ready 503, recover 200 | `ops/cert_chaos_results.json` 2026-09-07T12:36:39Z **PASS** for those two deps |
| Local restore RTO | 21.317 s after destroy_env | `ops/cert_restore_audit.json` |
| Managed PITR | `managed_postgres: false` | same |

Chaos **not run**: AI provider kill, billing provider kill, network partition, storage kill.

## Error handling (phase 8)

| Class | Behavior | Evidence |
| --- | --- | --- |
| HTTPException | `{error,status}` | `test_http_errors_are_structured` |
| Validation | Generic 422 | `test_validation_errors_do_not_echo_internals` |
| Unhandled | 500 generic + `unhandled_error` | `main.py` |
| Account storage delete | was silent; now `account_delete_storage_failed` | `auth.py` |
| Queue helper failures | now warning logs | `queue.py` |
| Poison mark-failed | `poison_job_mark_failed` if DB down | `tasks.py` |

Remaining silent-ish paths: `rq_worker.py` signal registration `except Exception: pass` (platform without SIGTERM); extractor/storage adapters log or map to 400.

No hidden crash handler was removed from the product UI this pass.

## Remaining reliability risk

- One stuck job after worker kill is **not** closed.
- 5k–50k analysis jobs unrun.
- Staging `REQUIRE_QUEUE=true` unrun.
- Restore is local Docker dump/restore, not managed PITR.

## Verdict

Local 1000-job and PG/Redis chaos **pass**. Worker-death **fail**. Reliability score stays **93 / 98** — not certified.
