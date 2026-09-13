# Required code changes (this pass vs remaining)

Date: 2026-09-07

## Implemented

| Area | Change |
| --- | --- |
| Circularity | `Metric.source`, `certifiable`, circular notes; template gold excluded from 98 |
| CIs | Wilson intervals on P/R/F1 in `eval.py` / `stats.py` |
| Held-out | `heldout_extra.py` (disciplines, malformed citations, thesis variants) |
| Citations | Reference-block skip; Harvard/Chicago; bibliography heuristic tightened; locators |
| Evidence | Two-author `(Author and Author, year)` treated as cited |
| Questions | Nested `explain` ignored after `to what extent` / `how far` |
| Arguments | `argument_structure()` flags (claim, reasoning, counter, rebuttal, gap) |
| Hallucination | Lecturer/study patterns; 1210-case suite |
| Verification | Crossref, OpenAlex, Semantic Scholar; never invent |
| Agreement | JSONL harness; empty file |
| Live eval | Status object, n_run=0 |
| Prompts | Registry + deploy reject without live scores |
| Calibration | Hard-label ECE; UI exposure false; n≥1000 to pass |
| Tests | `test_ai_eval_harness.py`; quality gate asserts nothing `certifiable` |

## Remaining (blocked on real data / keys, not more regex gold)

1. Commission ≥1000 lecturer-labeled items per analyzer (≥2000 citations).
2. Fill `reviewer_labels.jsonl` and publish κ.
3. Run `live_eval` for OpenAI / Anthropic / Gemini on 1000 examples (accuracy, latency, cost, schema, failures).
4. Labeled DOI verification set; measure precision/recall; persist `SourceVerification` in the analysis job **without** auto-marking unverified as verified.
5. Probability model if student-facing confidence is ever required; reliability diagrams on n≥1000.
6. Argument **relationship** gold (claim–evidence edges), not only paragraph flags.

Do not “complete” 98 by enlarging `*_gold()`.
