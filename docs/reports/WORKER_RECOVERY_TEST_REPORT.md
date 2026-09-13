# WORKER_RECOVERY_TEST_REPORT

**Measured:** 2026-09-13T21:20:27Z  
**Workers on ready:** 1  

## Expected

| Scenario | Expected |
| --- | --- |
| Worker online | `/api/ready` workers ≥ 1, jobs complete |
| Worker offline | With REQUIRE_QUEUE/staging, ready → 503 |
| Job failure | Job status failed; user sees retry copy |
| Retry | RQ retry / re-enqueue without silent loss |

## Actual (this harness)

Ready pass: **True**.  
Full chaos suite: run `python ops/cert_queue.py` and `python ops/cert_chaos.py` against staging Redis when Docker is healthy.

## Recommendations

1. Keep `restart: unless-stopped` on worker (compose).  
2. Alert when workers drop to 0 for >60s.  
3. Never mark staging ready without workers.
