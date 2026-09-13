# Database Scalability Report

Date: 2026-09-06  
Score: **70 / 100**  
Engine measured: **SQLite**  
Postgres + PgBouncer: configured in compose, **not benchmarked**

Query numbers: `docs/QUERY_BENCHMARK.md`.

## Schema / index audit

| Object | Current state | Root cause | Fix applied | Benchmark before | Benchmark after | Remaining risk |
| --- | --- | --- | --- | --- | --- | --- |
| Assignment list | Sort by `updated_at` per user, active rows | Filter + sort without covering key | Partial composite `ix_assignments_user_updated_active` (Alembic 005) | unmeasured | p95 **0.886 ms** at 100k rows | Postgres plan unknown |
| Document list | Same pattern | Same | `ix_documents_user_created_active` | unmeasured | not separately timed | Same |
| Report list | `user_id` + `created_at` | List/dashboard | `ix_analysis_reports_user_created` | unmeasured | not separately timed | Same |
| Finding page | `report_id` + time/severity | Pagination at volume | `ix_analysis_findings_report_created` + severity composite (004) | unmeasured | p95 **1.0 ms** at 500k | 1M / 5M / 10M not loaded |
| Jobs | Status filters | Dashboard | `ix_analysis_jobs_user_status` | unmeasured | none | 100k jobs untested |
| Joins | List N+1 on question/rubric/versions | Lazy ORM | `selectinload` | unmeasured query count | inferred O(1); no EXPLAIN | Postgres still required |
| Pagination | Already limit/offset or keyed page | Large dumps | Unchanged contract | n/a | findings page only | Offset deep page not timed |
| Pooling | Default SQLAlchemy | Connection storms | `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` + `pool_pre_ping` | none | none under HTTP | PgBouncer unhit |
| Prepared statements | SQLAlchemy default | Driver-dependent | Unchanged | n/a | n/a | Not isolated as a bench |
| PgBouncer | In `docker-compose.prod.yml` | Too many server conns | Transaction pool 200/20 | none | none | Not in this host path |

## Volume matrix

| Target | Status |
| --- | --- |
| 100,000 assignments | **Inserted and listed** |
| 1,000,000 findings | Not run |
| 5,000,000 findings | Not run |
| 10,000,000 records | Not run (500,000 findings is the max inserted) |

## Verdict

List and finding-page queries are **fast on SQLite at 100k / 500k**. That is why this category is 70 instead of the previous unmeasured 50s. It is **not** a Postgres 10M-row certificate, so 98 is refused.
