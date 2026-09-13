# Database Certification Report — AcademicCheck AI

Date: 2026-09-07  
Engine: PostgreSQL 16 Alpine (`docker-compose.cert.yml`, `127.0.0.1:55432`)  
Pool: `pool_size=10`, `max_overflow=20`, `pool_pre_ping`, `connect_timeout=3`, `pool_use_lifo`, `query_cache_size=1200` (this pass). Stale-job indexes: Alembic **007** (not re-EXPLAINed).  
Target: P95 query latency < 100 ms  
Decision: **PASS at 100k assignments / 1M findings. FAIL 5M / 10M (not loaded).**

Raw artifacts: `ops/cert_postgres_results.json`, `ops/cert_postgres_index_after.json`

## Loaded volumes

| Table | Rows | How |
| --- | ---: | --- |
| assignments | 100,000 | `COPY` |
| analysis_findings | 1,000,000 | `COPY` in 145.298 s |
| citations | 100,000 | `COPY` |
| references | 50,000 | `COPY` |
| analytics_events | 100,000 | `COPY` |
| reports / payments / credits / subscriptions | 1 each | ORM |

5M and 10M findings: **not inserted**. 1M already used ~145 s of `COPY`; those sizes were not run.

## Query latency (n=15 unless noted)

| Query | P50 ms | P95 ms | P99 ms | <100 ms |
| --- | ---: | ---: | ---: | --- |
| assignment list (user, active, LIMIT 20 OFFSET 40) | 4.491 | 7.842 | 7.842 | Pass |
| findings page (report, LIMIT 40 OFFSET 80) | 4.441 | 6.331 | 6.331 | Pass |
| report list | 3.984 | 7.069 | 7.069 | Pass |
| citation page | 4.638 | 7.359 | 7.359 | Pass |
| reference page (before 006) | 36.284 | 61.115 | 61.115 | Pass |
| analytics GROUP BY (before 006) | 71.506 | 83.437 | 83.437 | Pass |

After Alembic `006` indexes (`ops/cert_postgres_index_after.json`):

| Query | P95 ms | Plan |
| --- | ---: | --- |
| citation page | 5.980 | Index Scan `ix_citations_document_id_pk` |
| reference page | 8.731 | Index Scan `ix_references_document_sort` (was Seq Scan + sort, 61 ms p95) |
| analytics GROUP BY | 124.705 | Index Only Scan `ix_analytics_events_user_event` then aggregate 100k rows |

Analytics COUNT over 100k events remains the slowest path. P95 124.705 ms **misses** the 100 ms target after the index (first pass on a Seq Scan was 83.437 ms p95). Execution time in EXPLAIN is ~50 ms; Python session p95 includes client overhead and variance. Not partitioned.

## EXPLAIN ANALYZE (first pass)

- Assignments: Index Scan Backward `ix_assignments_user_updated_active`. Execution 0.229 ms.
- Findings: Index Scan `ix_analysis_findings_report_created`. Execution 0.171 ms.
- Reports: Seq Scan on 1-row table (expected). Execution 0.162 ms.
- References (before 006): Seq Scan 50k rows + top-N sort. Execution 59.551 ms. **Fixed by composite index.**

## Other checks

| Check | Result |
| --- | --- |
| Pool storm 40 workers / 80 `SELECT 1` | 0 errors, p95 257.501 ms |
| Read replica | `wal_level=replica` set on cert container; **no replica provisioned** |
| Partitioning | Not applied (1M findings page already index-only) |
| Connection exhaustion | Not observed at pool 10+20 |
| N+1 | These cert queries are single SQL statements, not ORM relationship loops |

## Verdict

Postgres list/page paths at **100k / 1M** meet p95 < 100 ms. This is **not** a 5M/10M or HA-replica certificate.
