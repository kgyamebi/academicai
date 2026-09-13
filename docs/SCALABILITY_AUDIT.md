# Scalability Audit Report

Date: 2026-09-07  
Previous overall: 69. **This pass overall: 69 / 100.** Gate 98. **Fail.**

No product features added. Fixes were hot-path only. Scores move only where a new benchmark exists.

Master certificate: `docs/SCALABILITY_CERTIFICATION.md`. Risk register: `docs/SCALABILITY_RISK_REGISTER.md`.

## Surfaces

| Surface | Bottleneck | Sequential? | Fix this pass | Measured |
| --- | --- | --- | --- | --- |
| Frontend | Unmeasured | n/a | none | no |
| API | 4 uvicorn workers saturate ~100 in-flight | request threads | GZip; ready cheaper; LIFO pool | cert_http 12:16Z |
| Workers | RQ SimpleWorker on Windows; analysis 209 jobs/min @5 | yes per job | SIGTERM graceful | not re-drilled |
| Redis | Single node AOF | — | client reuse on ready | ping 10k prior |
| Database | Single PG; offset lists | — | count query; no findings eager-load; 007 indexes | 1M prior; 007 un-EXPLAINed |
| Storage | Local filesystem | — | none | 10k prior |
| Extraction | In worker `process_job` | per document | none | prior AI cert |
| Analysis | Heuristic + optional LLM on worker | per job | none | 1000 jobs prior |
| Reporting | Findings paginated 40; PDF sync | PDF sync | stop eager-load all findings | code |
| Billing | Webhooks sync | — | none | pytest |
| Auth | Redis rate limit | — | none | pytest |
| Admin | Offset pages of 20 | — | none | unmeasured volume |

## HTTP this pass (`ops/cert_http_results.json`, 4 workers, Postgres)

| Path | In-flight | p95 ms | vs prior | SLO 500 ms |
| --- | ---: | ---: | --- | --- |
| `/api/live` | 1 | 10.4 | 13.8 | Pass |
| `/api/live` | 50 | **490** | 641 | **Pass this run** |
| `/api/live` | 100 | 1129 | 1197 | Fail |
| `/api/live` | 250 | 2747 | 3053 | Fail |
| `/api/live` | 500 | 3348 | 4893 | Fail |
| `/api/ready` | 1 | 103 | (new) | Pass |
| `/api/ready` | 50 | 2394 | 1692 | Fail |

Error rate 0% on all of the above. 1k/10k/50k concurrent users **not run**.

## Decision

Avoidable API overhead was reduced. The host still cannot hold p95 < 500 ms at 100 in-flight health checks. That is not a 1,000-user certificate.
