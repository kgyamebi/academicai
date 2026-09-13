# Bottleneck Elimination Report — AcademicCheck AI

Date: 2026-09-09  
Rule: no invented before/after HTTP numbers. SQL before/after uses `ops/cert_postgres_keyset.json` vs prior OFFSET behavior.

| Component | Root cause | Impact | Risk | Fix applied | Benchmark before | Benchmark after | Remaining risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Assignment list deep page | OFFSET walks prior rows | p95 234 ms at OFFSET 99980 | High | Keyset cursor + `ix_assignments_user_updated_id` | OFFSET 99980 p95 **234 ms** | Keyset after ~50k p95 **7.1 ms** | Clients that keep `page=` still OFFSET |
| Findings deep page | OFFSET 500k | p95 **1635 ms** | High | Keyset + `ix_analysis_findings_report_created_id` | OFFSET 500k p95 1635 ms | Keyset page 2 p95 **6.8 ms** | Same OFFSET fallback |
| Analytics GROUP | Seq/index-only over 100k | Was p95 124.7 ms FAIL | Medium | Covering `ix_analytics_events_user_event` (prior) | 124.7 ms (2026-09-07 after 006) | This pass p95 **34.2 ms** | Still full 100k index-only; no rollup table |
| Citation list | Per-reference verification SELECT | N queries | Medium | Group-by max(created_at) join | Unmeasured N+1 | Code + pytest; **no volume EXPLAIN** | LIMIT 200 still |
| Dashboard | Extra report query for trend | Extra round-trip | Low | One `LIMIT 12` fetch for trend + recent 8 | Unmeasured | Code inspection only | Still COUNT/AVG + docs + sub |
| Public FAQ/blog | DB on every anonymous GET | Read amplification | Low | 60 s process TTL | Unmeasured | Pytest cache hit | Stale 60 s; not Redis; not VU-tested |
| `/api/ready` | DB+Redis per probe | ready_50 p95 2394 ms | High | Worker enum already removed | ready_1 p95 103 ms | **No further HTTP re-bench this pass** | Stampede remains |
| `/api/live` 100-way | 4 workers one host | p95 1129 ms | Critical | GZip + LIFO pool (prior) | live_50 p95 490 ms pass | live_100 still fail | Need LB + replicas |
| Report GET findings | Eager-load all findings | Memory | Medium | Paginated (prior) | Code | Code | COUNT(*) per GET |
| PDF GET | Sync render | Thread block | Medium | **None** | Unmeasured | Unmeasured | S9 remains |
| RQ 50k | Time/Windows | Unknown loss | High | **None this pass** | 1000/1000 pass | 25k/50k **not_run** | S4 remains |
| Postgres SPOF | Single node | Outage | High | `wal_level=replica` only | n/a | replica **not_provisioned** | S6 remains |
| Local storage | No object store in cert | Upload SPOF | High | Signed URL code exists | 10k files | 100k **not_run** | S8 remains |
| Source verification lookup | Single-column index | Sort per ref | Low | Alembic 011 composite | UnEXPLAIN’d | UnEXPLAIN’d at volume | Apply 011 on prod |

Significant bottlenecks **not** eliminated: S1 API concurrency, S2 ready stampede, S4 queue volume, S5 10–50 workers, S6 replica/5M, S8 object storage, S9 PDF, live LLM.
