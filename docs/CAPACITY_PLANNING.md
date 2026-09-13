# Capacity Planning Report — AcademicCheck AI

Date: 2026-09-09  
Status: anchored on **cert_http** + PG 100k/1M keyset + RQ-1000 + `.txt` extract tiers. Extrapolation beyond that is labeled **guess**, not a measurement.

## Measured ceilings

| Fact | Value |
| --- | --- |
| `/api/live` 50 in-flight p95 | **490 ms** (SLO pass) |
| `/api/live` 100 in-flight p95 | **1129 ms** (SLO fail) |
| k6 100 VU mixed | p95 **1879 ms** |
| Assignment keyset p95 | **7.4 ms** at 100k rows |
| Findings keyset p95 | **6.8 ms** at 1M rows |
| Deep findings OFFSET 500k p95 | **1635 ms** — do not use |
| RQ analysis | 1000 jobs, **209/min**, 5 workers |
| Local files | 10k |
| Very-large `.txt` extract | **1416 ms**, ~3.8 MiB tracemalloc peak |

Certified published maximum: **do not sell 1,000 concurrent users from a box that misses p95 at 100 health-check in-flight.**

## Forecast (not a cluster measurement)

| Users | Concurrent ~5% | CPU | RAM | Storage | Bandwidth | DB growth | Queue | AI / provider $ |
| ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 1,000 | ~50 | May fit this PC for **health** only | Unmeasured | Unmeasured | Unmeasured | 100k assignments proven for list | 209 analysis/min proven | **Unknown** (heuristic only) |
| 10,000 | ~500 | live_500 p95 3.3 s here | Unmeasured | Unmeasured | Unmeasured | Guess | Unmeasured | Unmeasured |
| 50,000 | ~2,500 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Guess | Unmeasured | Unmeasured |
| 100,000 | ~5,000 | Unmeasured | Unmeasured | Unmeasured | Unmeasured | 5M/10M **not loaded** | Unmeasured | Unmeasured |
| 250,000 | — | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured |
| 500,000 | — | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured | Unmeasured |

Empty cells are **FAIL**, not zeros.

Scale-out sketch (guidance only): ≥2 API behind LB, PgBouncer, worker replicas on queue depth, managed Postgres + replica, managed Redis, object storage. **None of that topology was load-tested.**

## Verdict

**64 / 100.** Raise only after k6 1000+ on a load-balanced staging API including authenticated assignment/report paths and a live provider cost model.
