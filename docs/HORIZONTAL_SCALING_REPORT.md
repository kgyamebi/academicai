# Horizontal Scaling Report

Date: 2026-09-07  
Load balancer: **none** (client round-robin across two local uvicorn processes)

Artifact: `ops/cert_horizontal_results.json`

## Instance matrix

| Instances | Setup | Requests | P50 ms | P95 ms | P99 ms | Error rate | Status |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 × 4 workers | cert_http `/api/live` | see load report | — | 641 at 50 in-flight | 884 | 0% | Measured |
| 2 × 1 worker | ports 8015 + 8016 | 400 | 583.232 | 1094.74 | 1575.188 | 0% | Measured, p95 miss |
| 5 | — | — | — | — | — | — | **Not run** |
| 10 | — | — | — | — | — | — | **Not run** |
| 50 | — | — | — | — | — | — | **Not run** |

Nginx, Traefik, and a cloud load balancer were **not** deployed. Session integrity, JWT across a real LB, rate-limit clustering, uploads, and webhooks under multi-instance load were **not** tested.

JWT is stateless (shared secret). Prompt cache and `/api/metrics` remain **process-local**.

## Verdict

Two processes answered `/api/live` with 0% errors and p95 1.09 s. **Horizontal scaling is not certified** at 5/10/50 instances or behind an LB.
