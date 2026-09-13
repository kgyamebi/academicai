# Resilience Report

Date: 2026-09-07  
Chaos artifact (prior): `ops/cert_chaos_results.json`

| Failure | Proven | Continuity |
| --- | --- | --- |
| Redis down | live 200, ready 503, recover 200 | Health only |
| Postgres down | live 200, ready 503, recover 200 | Health only |
| Worker crash / SIGKILL | 11/12 jobs completed, 1 queued stuck | **Fail zero-stuck** |
| Network degradation | **not run** | — |
| AI provider outage | pytest circuit; no live keys | Heuristic fallback |
| Storage outage | **not run** | — |
| Billing provider | keys absent; checkout 503 | Fail-closed |
| Restore | 5× pg_restore, RTO 21.3 s local | Not managed PITR |

Blue-green: local proxy drill prior (`cert_bluegreen_results.json`). Cloud rolling/blue-green **not** this pass.

Retry: RQ 15/60/180. Enqueue fail-closed without Redis/workers.

**Not a 99.95% or multi-AZ certificate.**
