# Statistical validity review

Date: 2026-09-07  
Source: `eval_report.json`

## Estimators

| Quantity | Method | Notes |
| --- | --- | --- |
| Precision | tp / (tp+fp) | Wilson 95% CI on tp out of (tp+fp) |
| Recall | tp / (tp+fn) | Wilson 95% CI on tp out of (tp+fn) |
| F1 | harmonic mean of P and R | If every error is counted as both FP and FN (exact-match suites), F1 = accuracy and CI is Wilson on tp/n. Otherwise F1 CI is Wilson on round(F1×n)/n — a **crude** interval, not a bootstrap of the F1 functional |
| Kappa | Cohen / Fleiss in `stats.py` | **Not computed on real reviewers** (n=0) |
| Calibration | ECE / Brier treating hard labels as p=1.0 | Diagnostic only; UI confidence disabled; pass requires n≥1000 |

## Why 98% is not supported

Certification requires the **lower** bound of the 95% CI ≥ 0.98 **and** independent n ≥ 1000 (citations 2000).

Wilson 95% lower bound for 0 errors:

| n | Lower bound (approx.) | ≥0.98? |
| ---: | ---: | --- |
| 20 | 0.84 | No |
| 35 | 0.90 | No |
| 22 | 0.85 | No |
| 1000 | 0.996 | Yes *if* 0 errors *and* labels are independent gold |

Current held-out n is 17–35. Even a perfect classifier cannot certify 98% at these sizes.

Template suites have huge n and tight CIs around 1.00. Those CIs measure **rule consistency**, not correctness. They are excluded (`source: circular`, `certifiable: false`).

## Multiple testing / selection

Held-out extras were written to exercise the same writing-centre rules (strong/weak/missing, four-way evidence). They are independent of `*_gold()` templates but are **not** a random sample of student work and **not** lecturer-blind. Do not generalise F1=1.00 to production traffic.

## Verification and live LLM

Precision/recall for Crossref/OpenAlex/Semantic Scholar are **null**. Reporting 0.98 there would be fabrication.

Live provider accuracy, latency, cost, schema compliance: **n_run=0**.

## Decision

Statistically valid 98% certification: **not possible** with present independent n, absent reviewer labels, and absent live model eval.
