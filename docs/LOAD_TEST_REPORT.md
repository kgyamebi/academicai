# Load Testing Report

Date: 2026-09-07  
This pass artifact: `ops/cert_http_results.json` (12:16Z).  
Prior k6: `ops/cert_k6_summary.json` (PROFILE=100, not re-run).

## Steady / burst (health only)

| Concurrent | Tool | p95 | p99 | Errors | Notes |
| ---: | --- | ---: | ---: | ---: | --- |
| 1 | cert_http live | 10.4 ms | 20 ms | 0% | Pass |
| 50 | cert_http live | **490 ms** | 676 ms | 0% | p95 SLO pass this run |
| 100 | cert_http live | 1129 ms | 1564 ms | 0% | Fail |
| 250 | cert_http live | 2747 ms | 3660 ms | 0% | Fail |
| 500 | cert_http live | 3348 ms | 4080 ms | 0% | Fail |
| 50 | cert_http ready | 2394 ms | 2961 ms | 0% | Fail |
| 100 VUs × 3 min | k6 live+ready | 1879 ms | — | 0% | Fail p95; ~72 req/s |

Sustained authenticated load, uploads, report generation, and analysis jobs **were not** in HTTP/k6. Queue load is separate (`cert_queue_results.json` 1000 jobs).

## Capacity (measured ceiling)

This workstation + 4 uvicorn workers: **p95 < 500 ms holds at 50 in-flight `/api/live`, not at 100.**

## Bottlenecks observed

1. Worker count (4) vs in-flight (100+): queueing delay dominates.
2. `/api/ready` still does Postgres + Redis; 50-way p95 > 2 s.
3. Single host, no load balancer.

CPU/memory/storage latency during HTTP: **not sampled** (no host metrics agent).

1k / 10k / 50k concurrent users: **not run**.
