# Performance Report — AcademicCheck AI

Date: 2026-09-07  
Rule: cite measured artifacts only. Unrun 1k–50k user tests fail.

## API / process

Artifact: `ops/cert_http_results.json` (2026-09-07T12:16:16Z), uvicorn 4 workers, Postgres 16 Docker, SLO p95 500 ms.

| Probe | In-flight | p95 ms | vs SLO |
| --- | ---: | ---: | --- |
| `/api/live` | 1 | 10.368 | pass |
| `/api/live` | 50 | 490.28 | pass |
| `/api/live` | 100 | 1129.311 | **fail** |
| `/api/live` | 250 | 2747.283 | fail |
| `/api/live` | 500 | 3348.052 | fail |
| `/api/ready` | 1 | 103.07 | — |
| `/api/ready` | 50 | 2394.125 | fail vs 500 ms |

k6 (`ops/cert_k6_summary.json`): 100 VU max, `http_req_duration` p95 **1878.84 ms**, checks 13016/13016, failed-request rate 0. Threshold `p(95)<500` is recorded `true` in the k6 JSON **while p95 is 1878 ms** — treat the numeric p95 as the evidence, not the threshold flag.

Authenticated k6, 1000 / 10000 / 50000 concurrent users: **not run**.

## Database

See `docs/ENGINEERING_DATABASE_REPORT.md`. List/findings p95 &lt; 10 ms at 100k/1M (prior EXPLAIN). 5M/10M **not loaded**.

## Queue / workers

`ops/cert_queue_results.json`: 1000 analysis jobs, 5 workers, 209.2 jobs/min, 0 lost/dup/stuck. 5k/10k/50k analysis **not run**. Ping 5k/10k passed; 50k ping not completed.

## Frontend

No new bundle/CPU profile this pass. Playwright a11y exercises routes; that is not a performance budget. `frontend/lib/api.ts` aborts fetches (60s; 180s uploads) — timeout hardening, not a latency benchmark.

## Uploads / PDF / reports

- Uploads: size and type guards in `documents.py`; no new throughput number.
- PDF: still generated on the API thread (`download_pdf`). No PDF RPS benchmark this pass.
- Report GET: findings paginated (avoids loading all findings). No new report-GET p95 this pass.

## This-pass code (not a new benchmark)

- Public list caps (avoid unbounded serialize).
- Report ownership helper + score eager-load (avoids extra lazy queries; not a claimed ms win).

## Remaining slow paths (unmeasured or failed)

- `/api/live` at ≥100 in-flight.
- `/api/ready` at 50 in-flight (deep health).
- Sync PDF.
- Heuristic `engine.py` CPU per job (covered by job throughput 209.2/min at n=1000, not by a profiler dump).

## Verdict

Performance is **not** SLO-certified at 100 concurrent live probes. Do not cite an estimated improvement from the query refactors.
