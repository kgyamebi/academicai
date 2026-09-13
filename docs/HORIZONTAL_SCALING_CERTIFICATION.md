# Horizontal Scaling Certification — AcademicCheck AI

Date: 2026-09-09  
Gate: 5 / 10 / 25 / 50 instances behind a real load balancer with p95 &lt; 500 ms. **FAIL.**  
Artifact: `ops/cert_horizontal_results.json` 2026-09-07T09:22:43Z. Domain score **55 / 98**.

## Design (code / compose) vs measured

| Plane | Design | Measured |
| --- | --- | --- |
| API | Stateless JWT; GZip; LIFO pool | 1 host 4 workers (`cert_http`); 2 processes round-robin |
| Workers | RQ consumers on shared Redis | 1 and 5 workers on one host |
| Redis | Single cert instance, AOF | Restart PONG (`cert_redis_restart.json`) — not Redis Cluster |
| Storage | S3 adapter optional | Local disk only |
| Database | One Postgres 16; `wal_level=replica` | **No replica attached** |
| Load balancing | None in cert | Client round-robin, **not** nginx/Traefik/ALB |

## Instance matrix

| Instances | Throughput / p95 | Error rate | Failure impact | Status |
| ---: | --- | ---: | --- | --- |
| 1 × 4 workers | live_50 p95 **490 ms** | 0% | host death = outage | Measured |
| 2 × 1 worker | p95 **1094.74 ms** (400 req) | 0% | one process fail untested | Measured, SLO miss |
| 5 | — | — | — | **Not run** |
| 10 | — | — | — | **Not run** |
| 25 | — | — | — | **Not run** |
| 50 | — | — | — | **Not run** |

Scaling efficiency 1→2: p95 **worsened** (490 ms on 4-worker single process vs 1095 ms on two 1-worker processes). Do not treat 2-instance p95 as a scale-out win.

Hidden local state: in-process AI dict, public TTL cache, Prometheus histograms. Must scrape every replica. Uploads stick to local disk unless S3 is configured.

## Verdict

**Not certified** for horizontal scale-out. Two processes answered `/api/live` with 0% errors and a failed p95. Cost efficiency unmeasured (no cloud bill).
