# Scalability Risk Register — AcademicCheck AI

Date: 2026-09-09  
Evidence-backed scalability score: **70 / 98**. Unrun sizes are **FAIL**, not estimates.  
Sources: `ops/cert_http_results.json`, `ops/cert_postgres_keyset.json` (2026-09-09T20:46:31Z), `ops/cert_queue_results.json`, `ops/cert_document_extract.json`, `ops/cert_k6_summary.json`, `ops/cert_horizontal_results.json`.

| ID | Area | Bottleneck / ceiling | Class | Evidence | Residual |
| --- | --- | --- | --- | --- | --- |
| S1 | API | p95 SLO 500 ms fails above ~50 concurrent `/api/live` on one host | **Critical** | `cert_http_results.json` live_100 p95 **1129 ms**; live_500 p95 **3348 ms** | 1k–50k VUs **not_run**; authenticated routes **not_run** |
| S2 | API | `/api/ready` stampede (SELECT 1 + Redis PING) | **High** | ready_50 p95 **2394 ms**; ready_1 p95 **103 ms** | LB must not use ready as a high-QPS probe |
| S3 | API / LB | Two API processes, client round-robin, not nginx | **High** | `cert_horizontal_results.json` p95 **1095 ms**; instances_5/10/50 **not_run** | No cloud LB |
| S4 | Queue | Analysis jobs unproven beyond 1k | **High** | 1000 analysis PASS; 5k/10k/25k/50k **analysis** not run | Ping 5k/10k is not analysis |
| S5 | Worker | Kill leaves stuck job; 10–50 workers unrun | **High** | `cert_worker_death.json` stuck=1; workers 2/10/25/50 **not_run** | CPU/RSS **not_sampled** |
| S6 | Database | No replica; 5M/10M not loaded | **High** | `read_replica` / `pgbouncer` in `not_run`; findings **1,003,333** only | Postgres SPOF |
| S7 | Database | Deep OFFSET on large lists | **High** | findings OFFSET 500000 p95 **1635 ms**; assignment OFFSET 99980 p95 **234 ms** | Clients must use keyset cursors |
| S8 | Storage | Local disk; S3/R2/100k files unrun | **High** | `cert_storage_results.json` 10k only | Node SPOF |
| S9 | PDF | Sync `build_pdf_report` on API thread | **Medium** | `reports.py` `download_pdf` | Request blocking; not moved (UX) |
| S10 | Pagination | OFFSET still used when `cursor` omitted | **Medium** | `assignments.py` / `reports.py` offset fallback | Keyset path measured PASS |
| S11 | AI cache | Process dict + Redis; cluster hit rate unmeasured | **Medium** | `ai/cache.py` Redis prefix `ai:cache:`; no multi-replica drill | Replica miss unknown |
| S12 | Document extract | Full file in memory; PDF/DOCX unrun | **Medium** | `.txt` tiers in `cert_document_extract.json`; `not_run` pdf/docx | Cold langdetect import ~8 s observed once |
| S13 | Redis | Single instance; `maxmemory 512mb` on cert only | **Medium** | cert compose | Queue + rate-limit SPOF |
| S14 | Pool | Storm n=40 p95 257 ms (prior) | **Medium** | `cert_postgres_results.json` | PgBouncer **not** in cert path |
| S15 | Frontend | Next.js / SSR unmeasured | **Low** | No k6 on UI | Unknown |
| S16 | Billing | Live PSP unmeasured | **Low** for scale | keys absent | Not throughput |
| S17 | Auth | Redis rate-limit in production | **Low** | fail-closed | Login VU unrun |
| S18 | Reporting | Findings paginated; COUNT still per GET | **Low** | `func.count(AnalysisFinding.id)` | Extra query per report GET |
| S19 | Lock timeout | `lock_timeout=10s` / `statement_timeout=30s` | **Low** | session connect_args | Contention **not profiled** |
| S20 | Citations | List capped at 200; no cursor | **Low** | `citations.py` LIMIT 200 | N+1 verification **removed** this pass |
| S21 | Public cache | 60 s process TTL only | **Low** | `app_cache.py` max 256 keys | Stale FAQ/blog up to 60 s; not Redis |

**Critical** = blocks “horizontally scalable SaaS” claims. S1 alone forbids selling 100+ concurrent users on this topology.

## SPOFs (measured or compose)

| SPOF | Scale impact |
| --- | --- |
| Single Postgres | All lists/writes |
| Single Redis | RQ + prod auth rate-limit |
| Single API host | HTTP p95 collapse at 100 in-flight |
| Local disk storage | Uploads |
| Process-local metrics | Lost on scale-out |

Do not treat this register as a flame-graph certificate. No cProfile/py-spy dump exists in `ops/`.
