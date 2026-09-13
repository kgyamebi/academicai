# Database Performance Report

Date: 2026-09-07  
Engine: PostgreSQL 16 Alpine `127.0.0.1:55432`  
Pool: size 10, overflow 20, `pool_pre_ping`, `connect_timeout=3`, **`pool_use_lifo=True`**, **`query_cache_size=1200`**  
PgBouncer: present in `docker-compose.prod.yml` (transaction, 200 client / 20 server). **Not in the cert compose path** (API talks to Postgres directly on 55432).

Decision: **PASS p95 < 100 ms at 100k assignments / 1M findings. FAIL 5M / 10M (not loaded). FAIL HA replica.**

## Volumes (unchanged; not re-COPY’d this pass)

| Table | Rows | Artifact |
| --- | ---: | --- |
| assignments | 100,000 | `cert_postgres_results.json` |
| analysis_findings | 1,000,000 | same |
| citations | 100,000 | same |
| references | 50,000 | same |
| analytics_events | 100,000 | same |

## Query p95 (prior EXPLAIN)

| Query | P95 ms | Plan |
| --- | ---: | --- |
| assignment list LIMIT 20 | 7.842 | index `ix_assignments_user_updated_active` |
| findings page LIMIT 40 | 6.331 | `ix_analysis_findings_report_created` |
| citation page | 5.980 after 006 | `ix_citations_document_id_pk` |
| reference page | 8.731 after 006 | `ix_references_document_sort` |

Pool storm n=40: p95 257.5 ms, errors 0.

## This pass (code, not new EXPLAIN)

- Assignment list COUNT no longer wraps a `selectinload` subquery.
- Report GET no longer `selectinload` all findings (memory hotspot on large reports).
- Alembic **007**: `(status, started_at)` and `(status, created_at)` on `analysis_jobs` for `reap_stale_jobs`. **Not re-measured** on the 1M DB.

Cursor pagination was not added (would change list API). Offset remains a residual at deep pages.

Prepared statements: SQLAlchemy compiled-cache `query_cache_size=1200` (driver-level prepared statements still depend on psycopg).

## Remaining

No replica, no 5M/10M, no PgBouncer in the measured cert stack, payments/subscriptions tables n=1.
