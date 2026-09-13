# Database Scalability Certification — AcademicCheck AI

Date: 2026-09-09  
Gate: p95 &lt; 100 ms at **5M/10M** rows + read replica + PgBouncer in the measured path. **FAIL.**

Score this domain: **85 / 98** (was 82). Raised only for keyset EXPLAIN + analytics p95 now under 100 ms at 100k events. **Not** a 5M/10M certificate.

Artifacts: `ops/cert_postgres_keyset.json` (2026-09-09T20:46:31Z), `ops/cert_postgres_results.json`, Alembic 004–011.

Engine: PostgreSQL 16 Alpine `127.0.0.1:55432`. Pool: size 10, overflow 20, LIFO, `query_cache_size=1200`, `statement_timeout=30s`, `lock_timeout=10s`. PgBouncer: **prod compose only**, not this cert.

## Volumes loaded

| Table | Rows | 500K | 1M | 5M | 10M |
| --- | ---: | --- | --- | --- | --- |
| assignments | **100,006** | n/a | not this table | **not loaded** | **not loaded** |
| analysis_findings | **1,003,333** | — | **yes** | **not loaded** | **not loaded** |
| citations | 100,005 | — | — | **not loaded** | **not loaded** |
| references | 50,000 | — | — | **not loaded** | **not loaded** |
| analytics_events | 100,000 | — | — | **not loaded** | **not loaded** |
| payments / credits / subscriptions | tiny | — | — | — | — |
| source_verifications | not volume-loaded | — | — | — | — |

## Indexes implemented

| Type | Name | Purpose |
| --- | --- | --- |
| Composite + partial | `ix_assignments_user_updated_id` (`deleted_at IS NULL`) | keyset DESC (user, updated_at, id) |
| Composite | `ix_analysis_findings_report_created_id` | findings keyset ASC |
| Partial | `ix_documents_user_created_id` | document lists |
| Composite | `ix_analysis_jobs_user_status` | job lists |
| Partial | `ix_assignments_user_updated_active` | assignment list (004/005) |
| Composite | `ix_analysis_reports_user_created` | report list |
| Composite | `ix_citations_document_id_pk` | citation page |
| Composite | `ix_references_document_sort` | reference sort |
| Covering (index-only) | `ix_analytics_events_user_event` | analytics GROUP |
| Composite | `ix_analysis_jobs_status_started` / `_created` | reaper |
| Composite | `ix_payments_user_created` | payment list |
| Composite | `ix_source_verifications_reference_created` | latest verification (Alembic **011**, **not EXPLAIN’d at volume**) |

## Query p95 — this pass (`cert_postgres_keyset.json`)

| Query | p50 ms | p95 ms | vs 100 ms | Plan summary |
| --- | ---: | ---: | --- | --- |
| assignment OFFSET 20 | 4.671 | **6.855** | PASS | Index Scan Backward `ix_assignments_user_updated_id` |
| assignment OFFSET 50,000 | 102.915 | **150.581** | **FAIL** | same index; 50k rows walked |
| assignment OFFSET 99,980 | 152.624 | **234.077** | **FAIL** | 100k rows walked; ~101k buffers |
| assignment keyset page 2 | 4.401 | **7.440** | PASS | Index Cond on ROW(updated_at, id) |
| assignment keyset after ~50k | 4.585 | **7.113** | PASS | Index Cond; 23 buffers |
| findings OFFSET 80 | 8.312 | **14.304** | PASS | keyset index |
| findings OFFSET 500,000 | 764.26 | **1634.568** | **FAIL** | 500k rows walked |
| findings keyset page 2 | 4.707 | **6.791** | PASS | Index Scan `ix_analysis_findings_report_created_id` |
| analytics GROUP | 29.942 | **34.185** | PASS | Index Only Scan `ix_analytics_events_user_event` |
| payments LIMIT 50 | 3.855 | **7.045** | PASS | `ix_payments_user_created` (tiny table) |

Leading operator was **not** a Seq-Scan-only plan on the queries in `leading_seq_scan_only` (all false).

N+1: citation list now batches latest `source_verifications` (group-by max `created_at`). **Not** EXPLAIN’d at 200 references × N verifications.

## Requested implementations vs status

| Item | Status |
| --- | --- |
| Composite / partial / covering indexes | Alembic 004–011 |
| Cursor pagination | **Implemented** on assignments + report findings; OFFSET remains for `page` without cursor |
| Connection pooling | SQLAlchemy pool **measured** previously; PgBouncer **unmeasured** |
| Prepared statements | SQLAlchemy compiled cache 1200; driver PREPARE **not traced** |
| Read-replica readiness | Connection string can point at a replica; **none provisioned** |
| Partitioning | `partitioned: false`. Strategy remains design-only until 5M load exists |
| Large table strategy | Keyset required beyond shallow OFFSET; 5M/10M **not loaded** |

## Verdict

**PASS** shallow list/findings/keyset p95 &lt; 15 ms at **100k assignments / 1M findings**.  
**PASS** analytics GROUP p95 **34 ms** at 100k events (prior covering-index load was 124.7 ms FAIL).  
**FAIL** deep OFFSET (proven: 234 ms / 1635 ms).  
**FAIL** 5M / 10M (not loaded).  
**FAIL** HA replica and PgBouncer in the measured path.  
**Not certified** as an enterprise database scale-out.
