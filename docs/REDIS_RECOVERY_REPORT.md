# Redis Recovery Report — AcademicCheck AI

Date: 2026-09-09  

## Configuration (cert / prod compose)

- Image: `redis:7-alpine`
- `appendonly yes` (AOF)
- Volume: `redis_data` / `cert_redis_data`

## Drills this pass

| Drill | Artifact | Result |
| --- | --- | --- |
| INFO persistence + PING + reconnect | `ops/cert_redis_recovery.json` | **PASS** (`aof_enabled=1`, rdb bgsave ok) |
| `docker restart` Redis container | `ops/cert_redis_restart.json` | **PASS** (PONG, AOF size retained) |
| Historical API ready 503 when Redis down | `ops/cert_chaos_results.json` (2026-09-07) | **PASS** then recover |

## Not proven

| Item | Status |
| --- | --- |
| AOF rebuild after **volume wipe** | UNPROVEN |
| Redis Sentinel / Cluster failover | UNPROVEN |
| RQ job payload survival after volume loss | UNPROVEN — use `ops/recover_jobs.py` for DB orphans |
| Persistence of rate-limit keys across wipe | N/A / acceptable loss |

## Queue coupling

Analysis durability for long jobs is primarily **Postgres `analysis_jobs` + heartbeat recovery**, not Redis alone. Redis loss ⇒ queue empty; orphaned `processing` rows recoverable once via `recover_orphaned_jobs`.

## Verdict

**PASS** process restart with volume retained + AOF enabled on cert stack.  
**FAIL** Redis HA / volume-loss AOF certification.
