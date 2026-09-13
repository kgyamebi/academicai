# Queue Reliability Report — AcademicCheck AI

Date: 2026-09-07  
Also: `docs/QUEUE_SCALABILITY_CERTIFICATION.md`, `docs/QUEUE_CERTIFICATION.md`.

## Implemented (code) — not the same as 50k proof

| Control | Where | Host-proven? |
| --- | --- | --- |
| Dead-letter | `analysis_dlq` + `record_poison_job` | Pytest; 1000-job DLQ depth 0 |
| Poison detection | `on_failure` → fail_job | Pytest |
| Backoff | Retry 3× 15/60/180 s | Code; 1000-job did not measure retry storms |
| Idempotent jobs | `job_id` + terminal status skip | Code + pytest `fail_job` idempotent |
| Dedup | `DuplicateJobError` | 1000 analysis `duplicate_ids: 0` |
| Job timeout | `job_timeout=600` | Config; kill drill used shorter window |
| Worker heartbeat | RQ worker TTL (library default) | **Not separately metered** |
| Visibility / lease | RQ started-state + 600s timeout | Kill left **1 queued** within 120 s |
| Recovery | `reap_stale_jobs` 900s | Pytest stale processing; kill drill **did not wait 900s** |
| Fail-closed enqueue | no workers / Redis | Pytest + chaos |

RQ is not Celery.

## Volume validation

| Jobs | Kind | Lost | Dup | Stuck | Result |
| ---: | --- | ---: | ---: | ---: | --- |
| 1,000 | analysis | 0 | 0 | 0 | **PASS** `cert_queue_results.json` |
| 5,000 | ping | 0 | n/a | 0 queued | PASS **ping only** |
| 10,000 | ping | 0 | n/a | 0 queued | PASS **ping only** |
| 50,000 | — | — | — | — | **FAIL unrun** |

Worker death: **FAIL** zero-stuck (`cert_worker_death.json`).

## Verdict

**Not queue-reliability certified** for enterprise (zero stuck + 50k analysis). Certified only at **1,000 analysis jobs** on that host.
