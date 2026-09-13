# Worker Reliability Report — AcademicCheck AI

Date: 2026-09-09  

| Control | Status | Evidence |
| --- | --- | --- |
| Heartbeat column | Yes | `AnalysisJob.heartbeat_at` |
| Orphan recover (MAX 1) then fail | Yes | `recover_orphaned_jobs` pytest |
| Stale reaper 900s | Yes | `reap_stale_jobs` + credit refund test |
| Graceful SIGTERM `request_stop` | Yes | `rq_worker.py` + prior SIGTERM test |
| Startup recovery | Yes | `recover_and_requeue_orphans` |
| DLQ + alert | Yes | `notify_worker_failure` |
| Job timeout 600s | Yes | RQ enqueue |
| Kill-restart 12/12 | **FAIL** | stuck=1 |

**PASS** worker recovery *design + pytest*. **FAIL** zero-stuck kill certification (HAL-15).
