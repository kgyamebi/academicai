# Performance Profiling Report

Date: 2026-09-06  
Method: source audit of every hot path + measured benches in `ops/bench_results.json` and `ops/bench_http_results.json`.  
No production profiler (py-spy, Postgres `pg_stat_statements`, Redis MONITOR, Chrome Performance) was attached to a staging cluster.

## Surfaces

| Surface | Current state | Root cause | Fix applied | Benchmark before | Benchmark after | Remaining risk |
| --- | --- | --- | --- | --- | --- | --- |
| Frontend (Next.js) | App Router pages; list/report fetch JSON | Client waits on API; no cluster RUM | None (no product change) | unmeasured | unmeasured | Dashboard/upload/report latency at 1k users unknown |
| Backend API | FastAPI + SQLAlchemy | Single-process saturation under in-flight > 50 | HTTP `observe_ms` histogram; list/report `selectinload` | TestClient sequential `/api/live` p95 34 ms | Live uvicorn sequential p95 **7.6 ms**; 50 in-flight p95 **282 ms** | Authenticated routes not profiled; 100 in-flight p95 1208 ms |
| Database | SQLite in this bench | Dev default; prod refuses SQLite | Composite / partial indexes (Alembic 004 + 005); pool knobs | list queries unmeasured | 100k list p95 **0.886 ms** | Postgres plan at 1M–10M unknown |
| Redis | Optional; fail-closed enqueue | Shared cache + queue on one URL | Connection pool `max_connections=64` | none | none | Memory / failover unmeasured |
| Queue / workers | RQ `analysis` + `analysis_dlq` | Jobs not running on this host | Stable `job_id` (no duplicate enqueue) | 0 jobs | 0 jobs | Lost/duplicate/stuck unknown |
| Storage | Local disk or S3 adapter | Local disk is a node ceiling | Path `..` rejected | none | none | R2/S3 100k-file throughput unknown |
| Document pipeline | Parse → paragraphs/sections | Sequential CPU on worker | `db.add_all` for paragraphs/sections | unmeasured | unmeasured | Large PDF extract not timed |
| PDF / report generation | Per-request render | CPU + storage write | Unchanged product path | unmeasured | unmeasured | Large-report p95 unknown |
| AI analysis | Heuristic engine + optional LLM | LLM is blocking HTTP on the worker | In-process prompt cache + circuit | cache unmeasured | 1000 cache hits **3.732 ms** total | Live token path unprofiled |

## Hotspots found (code, not a sampling profiler)

1. **LLM enhance** — blocking provider HTTP on the worker. Primary throughput ceiling once Redis is live.
2. **Single uvicorn process** — `/api/live` p95 crosses 500 ms between 50 and 100 in-flight on this host.
3. **SQLite write amplification** — 400k finding inserts took 81.19 s. That is a load-generator cost, not a list-query cost.
4. **Process-local cache and metrics** — lost on deploy; not a cluster cache.
5. **N+1 (fixed in source)** — assignment list and report get now `selectinload`. Postgres EXPLAIN was not run, so query-count reduction is inferred, not proven on Postgres.

## Memory / allocation / leaks

No heap dump, tracemalloc, or long soak was run. No leak is claimed. No leak is disproven.

## CPU hotspots (measured)

In-process heuristic `run_analysis` on a tiny sample: ~3–4 ms per job, 14–17k jobs/min at 1–25 threads. That is not a document-pipeline or LLM CPU profile.
