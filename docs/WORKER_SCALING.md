# Worker Scaling Report

Date: 2026-09-06  
What ran: in-process heuristic `run_analysis` with a thread pool (not RQ, not LLM, not Redis).  
Source: `ops/bench_results.json` → `workers`

## Measured (tiny sample document)

| Workers | Jobs | Elapsed s | Jobs / minute | Avg completion s |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 4 | 0.016 | 14,689.9 | 0.004 |
| 5 | 20 | 0.071 | 16,889.2 | 0.004 |
| 10 | 40 | 0.137 | 17,574.2 | 0.003 |
| 25 | 100 | 0.428 | 14,025.6 | 0.004 |
| 50 | — | — | — | **Not run** |
| 100 | — | — | — | **Not run** |

p95 completion and queue lag were not recorded (no queue). Memory and CPU process samples were not recorded.

## Interpretation

Throughput stayed in a 14–17k jobs/min band from 1 to 25 threads. That means the tiny heuristic job is not the limiter; thread overhead already appears at 25 (14,026 vs 17,574 at 10). These jobs are **milliseconds**, not real assignment analyses.

Autoscaling thresholds **cannot** be set from this table. A real worker’s limiter is LLM HTTP and document parse, not the heuristic kernel.

## Recommended (unvalidated) starting point

Until `ops/queue_load.py` runs against Redis:

- Do not publish HPA numbers.
- Compose default remains 2 worker replicas.
- Treat certified worker capacity as **unknown**.
