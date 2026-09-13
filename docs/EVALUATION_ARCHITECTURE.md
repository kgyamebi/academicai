# Evaluation architecture — AcademicCheck AI

Date: 2026-09-07  
Companion: `docs/EVALUATION_BOARD.md`

No student-facing features. Deterministic analyzers stay the production path.

## Layers

| Layer | Contents | Certifies 98%? |
| --- | --- | --- |
| L0 Regression canary | `*_gold()` template suites | No |
| L1 Frozen seed | `heldout.py` / `heldout_extra.py` | No (n too small) |
| L2 Public remap (future) | PERSUADE (argument/position), AAE (structure/major claim), ASAP traits (research only) after 100–300 review | No, until mapped + dual κ |
| L3 Gold | `reviewer_labels.jsonl` dual lecturers, n floors 1000/1000/1000/1000 | Yes, with CIs |
| L4 Live LLM | `live_eval.py` | Separate (schema/hallucination) |

## Analyzer routing of datasets

```
Thesis   ← L3 gold  | L2 AAE Major Claim + PERSUADE Position (remapped) | L1 held-out
Argument ← L3 gold  | L2 AAE relations + PERSUADE Claim/Counter/Rebuttal | L1 held-out
Evidence ← L3 gold  | L1 held-out only until citation-need labels exist
Rubric   ← L3 gold  | ASAP/ASAP++ correlation studies only | never template gold
```

TOEFL11 is out of this diagram.

## Immediate board actions (ops/eval only)

1. Do not ingest public CSVs into training.  
2. Legal review of PERSUADE NC-SA and AAE/TUD + ASAP/Kaggle + TOEFL11/LDC terms before any copy lands in the repo.  
3. Commission 100–300 record audits before any “gold” tag.  
4. Keep `reviewer_labels.jsonl` as the only path to lecturer agreement.
