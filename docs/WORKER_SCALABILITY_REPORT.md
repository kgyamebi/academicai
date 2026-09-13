# Worker Scalability Report

Date: 2026-09-07

Heavy work already runs in RQ (`run_analysis_job`): extract → analyze → optional LLM → persist. API `create_analysis` enqueues; inline `process_job` only when queue is not required (test/dev).

PDF download remains **synchronous** on the API (`build_pdf_report`). Moving it would change the download workflow; not done.

## Measured

| Workers | Jobs | Throughput | Lost/stuck |
| ---: | ---: | ---: | --- |
| 1 | 50 analysis | 52 jobs/min | 0/0 |
| 5 | 1000 analysis | 209.2 jobs/min | 0/0 |
| 2, 10, 25, 50 | — | **not run** | — |

CPU/RSS: not sampled.

## This pass

`rq_worker.py`: SIGINT/SIGTERM calls `request_stop` when present; Redis socket timeouts 5 s. **Kill drill not repeated.**

Autoscaling guidance (not a cluster measurement): scale workers on `academiccheck_queue_depth` and job latency, not on API RPS. LLM jobs are I/O bound; heuristic jobs are CPU bound. Windows uses `SimpleWorker` (no fork).

## Verdict

**68 / 100.** Horizontal worker gain 1→5 is measured. 10–50 workers, memory caps, and cancellation UX are unproven.
