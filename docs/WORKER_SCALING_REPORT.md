# Worker Scaling Report — AcademicCheck AI

Date: 2026-09-09  
Live RQ `run_analysis_job` vs Docker Redis + Postgres.  
Artifacts: `ops/cert_queue_results.json`, `ops/cert_workers_results.json`.  
CPU / memory: **`not_sampled_host_metrics`**. This pass did **not** re-run 1–50 worker curves.

## Requested comparison

| Workers | Jobs | Elapsed s | Jobs / min | Queue lag | Job completion | CPU | RSS | Scaling efficiency |
| ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 50 analysis | 57.699 | 52.0 | not gauged | 0 lost/stuck/dup | **not sampled** | **not sampled** | baseline |
| 2 | — | — | — | — | — | — | — | **Not run** |
| 5 | 1,000 analysis | 286.817 | 209.2 | — | 0/0/0 | — | — | 209.2 / (5×52) ≈ **0.80** vs naive 1-worker rate |
| 10 | — | — | — | — | — | — | — | **Not run** |
| 25 | — | — | — | — | — | — | — | **Not run** |
| 50 | — | — | — | — | — | — | — | **Not run** |

PDF workers, extraction workers, and reporting workers are **not** separate pools. Upload extract runs **in the API request**. PDF render runs **in the API request**. RQ timeout: `job_timeout=600`.

Autoscaling readiness: queue depth is scraped; **no HPA / KEDA experiment**. Resource isolation: cert compose is one Redis + one Postgres, not cgroup-limited workers.

## Verdict

1 → 5 workers increased measured analysis throughput on this host (**52 → 209 jobs/min**).  
**10 / 25 / 50 workers are unproven.** Do not publish HPA targets. Do not mix in-process heuristic 9k+/min (`cert_ai_results.json`) with RQ.
