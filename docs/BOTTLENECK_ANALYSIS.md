# Bottleneck Analysis

Date: 2026-09-06

| Bottleneck | Why it matters | Mitigated in code? | Measured? |
| --- | --- | --- | --- |
| Single uvicorn process | `/api/live` p95 exceeds 500 ms between 50 and 100 in-flight | Horizontal replicas exist in compose only | **Yes** — 50 pass / 100 fail |
| LLM enhance on the analysis worker | Minutes of blocking HTTP; cost | Fallback, circuit, prompt cache | Cache microbench only |
| Finding insert volume | 1m-row list without covering keys | Composite indexes added | **500k** SQLite page p95 1.0 ms; 1m–10m no |
| Assignment serialize N+1 | List page latency | `selectinload` | SQLite list p95 0.886 ms at 100k; no Postgres EXPLAIN |
| SQLite in test/dev | Not a prod path | Prod refuses SQLite | Yes (startup) |
| In-process metrics / AI cache | Lost on deploy; not cluster-wide | Documented | n/a |
| Local disk storage | Single-node ceiling | S3 backend exists | No 100k-file run |
| Single Redis | Queue + rate limit share one node | Fail-closed | No outage drill on host |
| RQ unproven | Lost/duplicate analysis | DLQ + job_id + Retry | **0 jobs** run |

Primary measured API ceiling on this workstation: **~50 concurrent `/api/live` requests per process**.  
Primary unproven product ceiling: **worker + LLM**, not the health endpoint.
