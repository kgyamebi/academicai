# AI Scalability Report

Date: 2026-09-06  
Score: **68 / 100**

## Measured

| Test | Result |
| --- | --- |
| In-process prompt cache, 1000 lookups (all hits after first fill in the bench harness) | **3.732 ms** total, **0.373 µs** per lookup (`ops/bench_results.json` → `ai_cache`) |

That proves the cache dict is not the limiter. It does not prove token savings on a live provider.

## Implemented (source, not a new product)

| Control | Behavior |
| --- | --- |
| Cache | TTL 300 s, process-local (`backend/app/services/ai/cache.py`) |
| Dedup of enqueue | RQ `job_id` equals analysis id |
| Routing / fallback | OpenAI → Anthropic → Gemini via `complete_with_fallback` |
| Circuit | 5 failures → open, 30 s cooldown |
| Batching | Not implemented (would change the product analysis contract) |
| Chunk optimization | Not changed |

## Issue record

| Field | Value |
| --- | --- |
| Current state | Repeat identical prompts can hit the in-process cache; first miss still calls a provider |
| Root cause | Provider HTTP + tokens dominate cost and latency |
| Fix applied | Existing cache + circuit; no prompt-shape change |
| Benchmark before | cache unmeasured |
| Benchmark after | 1000 hits in 3.732 ms |
| Remaining risk | Cache is not shared across API/worker replicas; LLM path and token totals unmeasured; no live OpenAI outage |

## Unnecessary / duplicate calls

Enqueue dedup prevents two RQ jobs for the same analysis id while the first is queued/started. Cross-replica cache misses can still cause duplicate **provider** calls for the same prompt. That remaining risk is why this category is 68, not the 98 target.
