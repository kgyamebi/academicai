# Evaluation dashboard design

Date: 2026-09-07

No in-app student dashboard was added (product-surface freeze). Operators use:

1. `backend/app/services/ai/eval_report.json` (machine-readable)
2. Cursor canvas `ai-quality-certification.canvas.tsx` (this pass)

## Required tiles (all from measured artifacts)

| Tile | Current value | Rule |
| --- | --- | --- |
| Question accuracy (held-out F1) | 1.00 n=35; CI low 0.901 | Show CI; fail if n<1000 or CI low<0.98 |
| Thesis | 1.00 n=20; CI low 0.839 | same |
| Argument | 1.00 n=17; CI low 0.816 | same |
| Evidence | 1.00 n=18; CI low 0.824 | confusion matrix in report |
| Citation | 1.00 n=22; CI low 0.851 | unlabeled robustness n=2440 separate |
| Hallucination escape | 0% of 1210 red-team; live n=0 | two numbers, never conflated |
| Schema compliance | unmeasured | live n_run |
| Model failure rate | unmeasured | live providers |
| Regression history | `eval_baseline.json` F1s | prompt v1.1.0 unevaluated live |
| Prompt versions | v1.1.0 | deploy blocked |
| Confidence intervals | per suite in JSON | do not chart template 1.00 as quality |
| Reviewer κ | n=0 | show “unmeasured” |
| Verification P/R | null | show “unmeasured” |

## Display rules

- Circular suites in a collapsed “consistency only” panel.
- Never show a single “98% AI quality” badge while `certification.certified` is false.
- Do not expose hard-label ECE as student confidence.
