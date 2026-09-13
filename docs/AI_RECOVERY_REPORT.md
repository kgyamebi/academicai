# AI Recovery Report — AcademicCheck AI

Date: 2026-09-07  
Core scoring is **heuristic** (`run_analysis`). LLM enrich/coach is optional via `complete_with_fallback` (`backend/app/services/ai/provider.py`).

Artifact: `ops/cert_ai_results.json` 2026-09-07T09:15:03Z — `engine: heuristic_run_analysis`, `live_provider: false`.  
Chaos `ai_provider_kill`: **not_run**. Live OpenAI/failover load: **not_run**.

## Audit

| Provider | In repo | Live drill |
| --- | --- | --- |
| Configured LLM list (`available_providers`) | Circuit per `provider.name` | **No** (`live_provider: false`) |
| Heuristic | Always | Load 1–100 parallel, 0 errors |

## Simulations requested

| Simulation | Result |
| --- | --- |
| Provider failure | Code: `record_failure` → circuit open; `complete_with_fallback` returns `None` after all fail. **Live kill unrun** |
| Timeout | Not a separate measured test |
| Rate limiting | Not drilled |
| Network loss | Chaos network_partition **not_run** |

## Mission checks

| Check | Proven? | Notes |
| --- | --- | --- |
| Graceful degradation | **Code + heuristic cert** | Analysis jobs do not require LLM. Enrich skip is `None`, not invented text |
| Safe failure | **Code** | Firewall/hallucination blockers exist; not an outage drill |
| Queue recovery | Independent RQ path | Worker death is **queue** DR (1 stuck) — not AI-specific |
| User communication | **No dedicated outage banner** | Product copy already says AI is not an official grade. No status page (OPS-20) |

Heuristic throughput on that host (not recovery): 100 parallel p95 **11.047 ms**, errors **0**. Do not use as an LLM SLA.

## Verdict

**FAIL** as live AI-provider recovery. **PASS** as “core analysis continues without LLM” **in code** and heuristic load. Do not certify multi-provider failover until `live_failover_load` runs.
