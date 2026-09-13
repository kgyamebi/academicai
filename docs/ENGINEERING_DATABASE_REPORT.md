# Database Optimization Report — AcademicCheck AI

Date: 2026-09-07  
Measured engine (prior drill): PostgreSQL 16 Alpine `127.0.0.1:55432`  
Schema migrations: Alembic `001`–`007`.

## Pool and session (code)

`app/db/session.py`:

- `pool_pre_ping=True`
- Postgres: `pool_size` / `max_overflow` from settings, `pool_recycle=300`, `pool_timeout=30`, `pool_use_lifo=True`, `query_cache_size=1200`
- `connect_timeout=3`
- `statement_timeout=30000`, `lock_timeout=10000`

PgBouncer is declared in `docker-compose.prod.yml`. **Not** in `docker-compose.cert.yml` (API talks to Postgres on 55432). Prepared statements: SQLAlchemy compiled cache; driver-level prepare depends on psycopg and was not separately benchmarked.

## Indexes (migrations)

| Rev | Indexes |
| --- | --- |
| 002–005 | Job/finding/list composites (`docs/DATABASE_PERFORMANCE_REPORT.md`) |
| 006 | Citation + analytics |
| 007 | `ix_analysis_jobs_status_started`, `ix_analysis_jobs_status_created` for `reap_stale_jobs` |

007 is **not** re-EXPLAIN’d on the 1M-row cert database in this pass.

## Query patterns audited

| Path | Pattern | N+1? | Pagination |
| --- | --- | --- | --- |
| `GET /api/assignments` | `selectinload` question, rubric+criteria, versions; **separate** `count(Assignment.id)` | No (eager) | OFFSET, page_size ≤ 50 |
| `GET /api/reports/{id}` | Eager scores; findings `LIMIT/OFFSET`; count findings | No findings dump | page_size ≤ 100 |
| `GET /api/reports/{id}/pdf` | Same ownership + scores load; extra `db.get(Assignment)` | One extra assignment fetch | n/a |
| Public share | Eager scores (this pass) | Was lazy scores; fixed | findings page_size 80, no page param (existing contract) |
| `GET /api/public/blog` | `limit(50)` (this pass) | n/a | Cap, not cursor |
| `GET /api/public/faqs` | `limit(100)` (this pass) | n/a | Cap |

Assignment list COUNT no longer wraps a `selectinload` subquery (prior pass; `test_assignment_list_uses_direct_count`).

## Prior measured p95 (not re-run this pass)

Source: `docs/DATABASE_PERFORMANCE_REPORT.md` / `ops/cert_postgres_results.json`

| Query | P95 ms | Plan |
| --- | --- | --- |
| assignment list LIMIT 20 | 7.842 | `ix_assignments_user_updated_active` |
| findings page LIMIT 40 | 6.331 | `ix_analysis_findings_report_created` |
| citation page | 5.980 | `ix_citations_document_id_pk` |
| reference page | 8.731 | `ix_references_document_sort` |

Volumes: 100k assignments, 1M findings. **5M / 10M not loaded. FAIL.**

Pool storm n=40: p95 257.5 ms, errors 0 (prior).

## Expensive counts

List endpoints still `COUNT(*)` per page. That is correct for the current JSON (`total`) and is an OFFSET-cost residual, not a silent table scan on the list query at 100k (EXPLAIN used the composite index).

## Serialization

Report GET paginates findings. It does **not** `selectinload` all findings (memory hotspot closed earlier). PDF still serializes the report in-process.

## Remaining

- No replica / HA.
- No PgBouncer on the measured cert path.
- OFFSET at deep pages.
- Payments/subscriptions tables were n=1 on restore audit.
- 007 indexes not re-measured.

## Verdict

PASS p95 &lt; 100 ms at 100k assignments / 1M findings (prior EXPLAIN). FAIL 5M/10M. FAIL HA replica. This pass adds public caps and report ownership/score loads; it does not claim a new EXPLAIN number.
