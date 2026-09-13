# AI quality gap analysis

Date: 2026-09-07  
Source: `backend/app/services/ai/eval_report.json`

**Evidence-backed AI quality: 87 / 100.** Gate **98. Fail. Not certified.**

87 is a one-point move from 86 for: circular suites excluded from certification, 95% CIs on every suite, citation held-out no longer 0.933, hallucination red-team n=1210, verification never-invent contract. It is **not** a 98 claim.

## Gaps versus the 98% standard

| Gate | Required | Measured | Gap |
| --- | --- | --- | --- |
| Question F1 (held-out, CI low) | ≥0.98, n≥1000 | F1 1.00, CI low **0.901**, n=**35** | n and CI |
| Thesis | ≥0.98, n≥1000 | F1 1.00, CI low **0.839**, n=**20** | n and CI |
| Argument | ≥0.98, n≥1000 | F1 1.00, CI low **0.816**, n=**17** | n and CI |
| Evidence | ≥0.98, n≥1000 | F1 1.00, CI low **0.824**, n=**18** | n and CI |
| Citation | ≥0.98, n≥2000 | F1 1.00, CI low **0.851**, n=**22** | n and CI |
| Reference verification precision | ≥0.98 | **null** (no labeled DOI set; APIs not scored) | unmeasured |
| Hallucination escape | <0.5% | Red-team 0/1210; **live LLM not run** | live unmeasured |
| Schema compliance | >99.9% | Live n_run=**0** | unmeasured |
| Reviewer agreement | Documented kappa | n=**0** | unmeasured |
| Calibrated confidence | ECE pass, n≥1000 | ECE 0 on n=55 hard labels; **not exposed**; **fail** n floor | n |

## What improved this pass (not 98)

- Citation extractor: skip in-text spans in References; stop treating ordinary year-sentences as bibliography; Harvard/Chicago patterns; two-author evidence cites.
- Question: do not treat “explain” as a second command inside “to what extent … explain”.
- Eval: CIs, circularity flags, `certifiable` requires held-out n floors and CI low ≥0.98.
- Hallucination: lecturer-expectation and fabricated-study patterns; 1210 block cases.
- Verification module: Crossref / OpenAlex / Semantic Scholar; empty lookup → `could_not_verify`. Never invents a match.
- Live eval harness records **unproven** when keys are absent (0/3).

## What was not done (correctly)

- No fabricated 1000-label datasets
- No fabricated lecturer reviews
- No 98% marketing claim
- No student-facing confidence scores

Point F1 of 1.00 on n≤35 is **consistency with a small expert set**, not a certified quality level.
