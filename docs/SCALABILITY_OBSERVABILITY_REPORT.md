# Scalability Observability Report — AcademicCheck AI

Date: 2026-09-09  
Scrape surface: `GET /api/metrics/prometheus` (process-local). No hosted Grafana / OTel collector in this cert.

## Metrics implemented

| Signal | Metric / field | Notes |
| --- | --- | --- |
| API latency p50/p95/p99 | `academiccheck_http_latency_ms{quantile=...}` | Rolling in-process sample cap 2000 |
| Per-path p95 | `academiccheck_http_endpoint_p95_ms` | Cap 500 samples / path |
| Error rates | `academiccheck_http_errors_5xx_total` | Per path |
| Ready / DB / Redis | `academiccheck_ready`, `_database`, `_redis` | `/metrics` still runs deep ready |
| Queue lag (depth) | `academiccheck_queue_depth` | **Not age** |
| Worker count | `academiccheck_workers` | Cached ~2s |
| DB pool | `academiccheck_db_pool_size`, `_checked_out`, `_overflow` | Best-effort |
| Cache hit/miss rate | `academiccheck_cache_ai_hit_rate`, `_meta_hit_rate` (+ miss) | This pass; unscraped in prod |
| AI circuit | `academiccheck_circuit{name,state}` | Open/closed/half_open |
| Storage latency | **none** | FAIL |
| AI provider latency | **none** as a histogram | FAIL (only circuit + counters) |

JSON twin: `GET /api/metrics` includes `http_latency`, `endpoints`, `gauges`, `ai_circuits`.

## Dashboards requested

| Dashboard | Status |
| --- | --- |
| Operations | **Not deployed** (no Grafana) |
| Capacity | **Not deployed** |
| Performance | **Not deployed** |
| Scalability | **Not deployed** |

Docs `docs/OPERATIONS_DASHBOARDS.md` remain design. Pytest `test_observability_metrics.py` proves the text changes under simulated TestClient load, not under 10k VU.

## Verdict

**68 / 100.** Instrumentation exists. A scalability dashboard does **not**. Replica-local histograms cannot be summed without a collector.
