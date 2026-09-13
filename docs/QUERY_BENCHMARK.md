# Query Benchmark Report

Date: 2026-09-06  
Engine: **SQLite** file `backend/bench_scale.db`  
Postgres: **not run**

Source: `ops/bench_results.json`

## Insert volume (setup cost, not a query SLO)

| Step | Rows added | Elapsed |
| --- | ---: | ---: |
| assignments → 10,000 | 10,000 | 0.790 s |
| assignments → 50,000 | 40,000 | 3.772 s |
| assignments → 100,000 | 50,000 | 5.672 s |
| findings → 100,000 | 100,000 | 13.124 s |
| findings → 500,000 | 400,000 | 81.190 s |

Cumulative: **100,000 assignments** and **500,000 findings**.

Not inserted: 1,000,000 / 5,000,000 / 10,000,000 findings.

## Read queries (n = 15 samples each)

| Query | Rows in table | p50 ms | p95 ms | p99 ms | max ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Assignment list (user + `deleted_at IS NULL`, indexed) | 10,000 | 0.477 | 0.878 | 0.878 | 2.778 |
| Assignment list | 50,000 | 0.503 | 0.608 | 0.608 | 0.893 |
| Assignment list | 100,000 | 0.674 | 0.886 | 0.886 | 1.366 |
| Findings page (`report_id` + created_at) | 100,000 | 0.448 | 0.575 | 0.575 | 1.544 |
| Findings page | 500,000 | 0.441 | 1.000 | 1.000 | 1.069 |

All measured list/page p95 values are **under 2 ms** on this SQLite file. That supports “no list-query bottleneck at 100k/500k on SQLite.” It does not support a 10M-row Postgres claim.

## Indexes exercised

- `ix_assignments_user_updated_active` (`user_id`, `updated_at`) WHERE `deleted_at IS NULL`
- `ix_analysis_findings_report_created` (`report_id`, `created_at`)
- Also present in schema/migrations, not separately timed: `ix_documents_user_created_active`, `ix_analysis_reports_user_created`, `ix_analysis_jobs_user_status`, `ix_analysis_findings_report_severity`

## Not run

- `EXPLAIN (ANALYZE, BUFFERS)` on PostgreSQL
- Joins for dashboard / compare / admin at volume
- Full-text search
- Large-report payload serialize (findings page was a keyed page, not a 10k-row dump)
