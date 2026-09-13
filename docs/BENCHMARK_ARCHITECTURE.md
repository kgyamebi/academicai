# Benchmark architecture

Date: 2026-09-07

```
                    ┌─────────────────────────────┐
                    │  Production classifiers     │
                    │  question / thesis / arg /  │
                    │  evidence / citations /     │
                    │  hallucination guard        │
                    └─────────────┬───────────────┘
                                  │
          ┌───────────────────────┼────────────────────────┐
          ▼                       ▼                        ▼
 ┌─────────────────┐    ┌─────────────────┐      ┌─────────────────┐
 │ Circular gold   │    │ Independent     │      │ Red-team /      │
 │ *_gold()        │    │ heldout*.py     │      │ unlabeled       │
 │ consistency     │    │ validity (small)│      │ robustness      │
 │ NOT 98          │    │ CIs; n<<floors  │      │ no F1 gold      │
 └────────┬────────┘    └────────┬────────┘      └────────┬────────┘
          │                      │                        │
          └──────────────┬───────┴────────────────────────┘
                         ▼
              eval.run_all + extras_bundle
                         ▼
              eval_report.json + eval_baseline.json
                         ▼
         certifiable iff held-out AND n floor AND CI low≥0.98
                         ▼
              certification.claim_98 = false (current)
```

## Components

| Component | Path |
| --- | --- |
| Metrics + CIs + verdict | `app/services/ai/eval.py` |
| Stats | `stats.py` |
| Reviewer JSONL | `agreement.py`, `reviewer_labels.jsonl` |
| Hallucination red-team | `hallucination_suite.py` |
| Citation robustness | `citation_corpus.py` |
| Live LLM (unrun) | `live_eval.py` |
| Prompt versions | `prompt_registry.py` / `prompt_registry.json` |
| Calibration diagnostic | `calibration.py` |
| Reference lookup | `analysis/verify_sources.py` |
| CI gates | `tests/test_ai_quality_gate.py`, `tests/test_ai_eval_harness.py` |

## Regression

`test_ai_quality_does_not_regress` fails if any baseline F1 drops more than 0.03 or floors fail. Template F1 remains a **consistency** floor, not a 98 certificate.

Prompt registry `allow_deploy` is **false** until live accuracy exists.
