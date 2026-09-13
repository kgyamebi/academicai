# Cache Architecture Report — AcademicCheck AI

Date: 2026-09-09  
This is a **design + unit-test** certificate, not a cluster hit-rate load test.

## Layers

| Layer | What | Invalidation | Evidence |
| --- | --- | --- | --- |
| Redis AI cache | `ai:cache:` + SHA256(prompt, strong) TTL `ai_cache_ttl_seconds` | TTL; `reset_cache()` SCAN delete | Heuristic 1000 hits in 3.849 ms (`cert_ai_results.json`) |
| In-process AI dict | max 512 keys, evict oldest 64 | TTL + size | Same file; lost on replica |
| Request collapsing | `take_leadership` / `publish_result` | Inflight map | Code; not multi-process |
| Public metadata | `app.core.app_cache` keys `public:faqs`, `public:blog`, TTL **60 s**, max 256 keys | TTL; `cache_clear()` on tests | Pytest: miss then hit (`cache.meta.hit` ≥ 1) |
| Query cache | SQLAlchemy `query_cache_size=1200` compiled statements | Process lifetime | Config; not hit-rate |
| HTTP | `Cache-Control: no-store` on API | n/a | Correct for tenant data |
| Sessions | JWT / cookie; not a Redis session cache | n/a | Auth scale unrun |
| Reports / assignments | **Not** cached (tenant-specific) | n/a | Keyset DB instead |

## Metrics

`/api/metrics/prometheus` gauges `academiccheck_cache_ai_hit_rate`, `academiccheck_cache_ai_miss_rate`, `academiccheck_cache_meta_hit_rate`, `academiccheck_cache_meta_miss_rate` after `refresh_runtime_gauges()`.

No production scrape of hit rate exists. Cluster hit rate: **FAIL (unmeasured)**.

## Latency reduction

Public FAQ second read is in-process (pytest). No millisecond comparison vs DB on Postgres was recorded for FAQ/blog.

## Verdict

Cache is **present** for AI responses and public lists. It is **not** a query-result Redis cache for assignments/reports. Do not claim a measured hit-rate SLO.
