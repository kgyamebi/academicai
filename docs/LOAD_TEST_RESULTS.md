# Load Test Results — AcademicCheck AI

Date: 2026-09-09  
HTTP numbers are **not re-run this pass**. Source: `ops/cert_http_results.json` 2026-09-07T12:16:16Z, `ops/cert_k6_summary.json`.

SLO: p95 &lt; 500 ms, p99 &lt; 1000 ms, error rate &lt; 1% on the measured path.

## A. Live uvicorn — `GET /api/live`

Process: 4 uvicorn workers, Docker Postgres. Path is liveness only.

| In-flight | Requests | p50 ms | p95 ms | p99 ms | Error rate | p95 &lt; 500 | p99 &lt; 1000 |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 1 | 200 | 6.868 | 10.368 | 20.111 | 0.0 | Pass | Pass |
| 50 | 500 | 209.536 | 490.28 | 675.698 | 0.0 | Pass | Pass |
| 100 | 1000 | 483.781 | 1129.311 | 1564.019 | 0.0 | **Fail** | **Fail** |
| 250 | 1000 | 1181.978 | 2747.283 | 3659.909 | 0.0 | **Fail** | **Fail** |
| 500 | 1000 | 1686.207 | 3348.052 | 4080.452 | 0.0 | **Fail** | **Fail** |
| 1,000–50,000 | — | — | — | — | — | **Not run** | **Not run** |

## B. k6 mixed live + ready (PROFILE=100)

| Metric | Value |
| --- | --- |
| Max VUs | 100 |
| p50 / med | 298.6 ms |
| p95 | **1878.8 ms** |
| max | 2868.9 ms |
| http_req_failed | 0 (checks 13016 pass / 0 fail) |
| Threshold p(95)&lt;500 | **failed** |

Profiles 1000 / 5000 / 10000 / 50000: **not run**.

## C. Other test types requested

| Type | Status |
| --- | --- |
| Load (health) | Partial — table A |
| Stress | live_500 only |
| Concurrency | in-flight 1–500 |
| Burst / spike | **Not run** as a named profile |
| Soak | **Not run** |
| Authenticated dashboard / upload / analysis / PDF | **Not run** |
| Database under HTTP load | PG keyset is offline SQL, not under HTTP |
| Queue under HTTP enqueue storm | **Not run** |
| Storage under HTTP upload storm | **Not run** |

## Verdict

**FAIL** as a production load certificate. The only SLO pass is `/api/live` at 50 in-flight on this workstation.
