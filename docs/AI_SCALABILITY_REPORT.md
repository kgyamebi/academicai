# AI Scalability Report — AcademicCheck AI

Date: 2026-09-09  
Engine measured: in-process heuristic `run_analysis`. `live_provider: false`.  
Artifact: `ops/cert_ai_results.json` 2026-09-07T09:15:03Z. **No live 100–10,000 concurrent provider run this pass.**

## Audit

| Piece | Implementation | Scale evidence |
| --- | --- | --- |
| Prompt generation | registry + `wrap_untrusted` | Unrun live |
| Caching | Redis `ai:cache:` when Redis up; in-process TTL dict max 512; request collapsing via `take_leadership` | 1000 heuristic cache hits in **3.849 ms** |
| Chunking | Document paragraphs; LLM is excerpt/fallback | Not distributed map-reduce |
| Provider failover | `complete_with_fallback` + per-name circuit | `live_failover_load not_run` |
| Cost controls | circuit + timeouts; no token-budget load test | Unrun |
| Dedup / collapsing | in-process futures; not a cluster singleflight | Unrun multi-replica |

## Heuristic parallel (not LLM)

| Parallel | P50 ms | P95 ms | Errors | / min |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 4.053 | 4.053 | 0 | 2,126 |
| 10 | 4.042 | 4.427 | 0 | 3,850 |
| 50 | 4.258 | 11.547 | 0 | 9,218 |
| 100 | 3.916 | 11.047 | 0 | 9,975 |
| 1,000 / 5,000 / 10,000 | — | — | — | **Not run** |

Queue impact of live LLM: **not measured**. Provider cost: **not measured**.

## Verdict

Heuristic cache and 100-way in-process analysis are **not** a live OpenAI/Anthropic certificate.  
**FAIL** 1k / 5k / 10k concurrent analyses against a real provider.
