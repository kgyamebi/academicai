# API Scalability Report — AcademicCheck AI

Date: 2026-09-09  
HTTP load artifact (unchanged this pass): `ops/cert_http_results.json` 2026-09-07T12:16:16Z (uvicorn **4** workers, Docker Postgres).  
k6: `ops/cert_k6_summary.json` 100 VU mixed `/api/live`+`/api/ready` (threshold `p(95)<500` **failed** at p95 **1879 ms**).  
Horizontal: `ops/cert_horizontal_results.json` (2 processes, **not** nginx).

API scale subscore remains **63 / 100**. Gate 98. **FAIL.**  
No new 100 / 1,000 / 5,000 / 10,000 / 50,000 concurrent-user run was executed this pass.

## Endpoint classes (audit)

| Class | Blocking / N+1 / payload | Evidence |
| --- | --- | --- |
| `/api/live` | Cheap JSON | Load table below |
| `/api/ready` | DB + Redis ping | ready_50 p95 2394 ms |
| Assignment list | Keyset when `cursor` set; OFFSET fallback; `selectinload` question/rubric/versions | Pytest cursor pages; PG keyset p95 7.4 ms |
| Report GET | scores `selectinload`; findings LIMIT + optional cursor; COUNT(*) | Code; not in k6 |
| Report PDF | **sync** `build_pdf_report` | Not load-tested |
| Dashboard | 1 report slice (12 rows) + counts + docs; plan via subscription | Code this pass; **not** HTTP-benched |
| Citations GET | LIMIT 200; batched verifications | Code; **not** HTTP-benched |
| Public blog/FAQ | 60 s process TTL cache | Pytest cache hit; **not** VU-benched |
| Payments | LIMIT 50 | PG p95 7.0 ms on tiny table |
| Metrics Prometheus | process-local; `/metrics` still deep-ready | Stampede risk |
| Auth / billing | Redis limiter; checkout 503 without keys | Unrun at VU scale |

GZip: `GZipMiddleware` min 500. Tenant API `Cache-Control: no-store`. Streaming: upload read in 1 MiB chunks; PDF is **not** streamed. Timeouts: DB 30s statement; Redis socket 2s; AI HTTP `ai_timeout_seconds=90`.

## Concurrent load (`/api/live`, error_rate 0.0)

| In-flight | Requests | P50 ms | P95 ms | P99 ms | vs SLO p95 500 |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 200 | 6.868 | 10.368 | 20.111 | Pass |
| 50 | 500 | 209.536 | **490.28** | 675.698 | Pass (p95) / Fail p99&lt;1000? p99 676 pass |
| 100 | 1000 | 483.781 | **1129.311** | 1564.019 | **Fail** |
| 250 | 1000 | 1181.978 | 2747.283 | 3659.909 | **Fail** |
| 500 | 1000 | 1686.207 | 3348.052 | 4080.452 | **Fail** |
| 1,000 | — | — | — | — | **Not run** |
| 5,000 | — | — | — | — | **Not run** |
| 10,000 | — | — | — | — | **Not run** |
| 50,000 | — | — | — | — | **Not run** |

k6 PROFILE=100: max VUs 100, http_req_duration p95 **1878.8 ms**, checks 13016/0, `p(95)<500` **failed**.

Authenticated assignment/report/upload/analysis paths: **not measured**.

## Verdict

**PASS** `/api/live` at 50 in-flight p95 &lt; 500 ms on this workstation.  
**FAIL** 100+ in-flight, k6-100 mixed live+ready, and every requested VU tier above 100.  
Do not claim API capacity for 1,000–50,000 concurrent users.
