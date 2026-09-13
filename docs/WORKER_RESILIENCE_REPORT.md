# Worker Resilience Report — AcademicCheck AI

Date: 2026-09-07  
Artifacts: `ops/cert_worker_death.json`, `ops/cert_workers_results.json`, `backend/app/workers/rq_worker.py`.

## Implemented

| Control | Status | Proven? |
| --- | --- | --- |
| Graceful shutdown | SIGINT/SIGTERM → `request_stop` | Code; **SIGKILL drill used kill** |
| Automatic restart | prod compose `restart: unless-stopped` (this pass) | **Not chaos-tested** |
| Crash recovery | Replacement worker in death drill | 11/12 completed |
| Work reassignment | RQ timeout / reaper 900s | **1 still queued at 120 s** |
| Health / heartbeat | RQ Worker.all; ready does **not** enumerate workers every request | Count cached 2s |
| Isolation | Separate worker process vs API | Compose `worker` service |
| Memory / CPU pressure | — | **Not run** |
| Network interruption | — | **Not run** |

Windows uses `SimpleWorker` (no fork).

## Kill-during-processing

12 jobs, kill after ~3 s, replacement started: completed **11**, queued stuck **1**, `pass: false`.

Restart workers: implied by replacement process in that drill — **not** compose `restart` policy (added later, untested).

## Verdict

**FAIL** worker fault-tolerance vs “jobs complete safely” under SIGKILL. Steady 1k jobs with 5 live workers **PASS**.
