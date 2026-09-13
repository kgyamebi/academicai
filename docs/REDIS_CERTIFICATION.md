# Redis Certification Report

Date: 2026-09-06  
Status: **not certified**  
Score is folded into Queue (50) and Observability (64); this report records Redis-specific evidence only.

## Implemented in source

| Item | Current state | Root cause | Fix applied | Benchmark before | Benchmark after | Remaining risk |
| --- | --- | --- | --- | --- | --- | --- |
| Connections | New client per use historically | Unbounded sockets under workers | Singleton + `max_connections=64` | unmeasured | unmeasured | Pool saturation under 50k jobs unknown |
| Queue + cache share | One `REDIS_URL` | Operational coupling | Unchanged (no product split) | n/a | n/a | Cache eviction can still affect RQ if mis-keyed |
| Eviction | Host default | Unset in app | Not set in application code | none | none | Must be `allkeys-lru` or reserved RQ prefix on the host |
| Failover | Single URL | One node | Fail-closed enqueue | pytest: enqueue false | same | Sentinel/Cluster not configured |
| Monitoring | ping via `/api/ready` | No Redis INFO export | Ready 503 when required | injection tests | injection tests | Memory pressure not graphed |

## Required validations — not run

| Scenario | Result |
| --- | --- |
| High concurrency (1k–50k jobs) | Not run |
| Cache growth | Not run |
| Queue growth | Not run |
| Memory pressure / eviction | Not run |
| Redis restart / failover | Not run |

## Verdict

Redis is a **single point of failure** in the current compose/design until a replica or managed failover is provisioned and drilled. Code fail-closed is proven; host failover is not.
