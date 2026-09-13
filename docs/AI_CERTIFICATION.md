# AI Quality Certification — AcademicCheck AI

Date: 2026-09-07  
Previous score: 86. **Evidence-backed score: 87 / 100.** Gate 98. **Fail.**  
`eval_report.json` → `certification.claim_98 = false`.

Rule: no 98 claim without independent n floors, CI lower bound ≥0.98, lecturer labels, and live LLM eval.

See also: `CIRCULARITY_AUDIT.md`, `AI_QUALITY_GAP_ANALYSIS.md`, `STATISTICAL_VALIDITY_REVIEW.md`, `AI_CERTIFICATION_READINESS.md`.

## 1. Why 98 is refused

Template F1 ≈ 1.00 is **circular**. Held-out point F1 is 1.00 on n=17–35; **every 95% CI lower bound is below 0.95**. Reviewer labels n=0. Live LLM n_run=0. Verification precision null.

## 2. Held-out (independent expert-constructed — not lecturer gold)

| Suite | n | P | R | F1 | F1 CI low | Certifiable |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Question | 35 | 1.000 | 1.000 | 1.000 | 0.901 | No |
| Thesis | 20 | 1.000 | 1.000 | 1.000 | 0.839 | No |
| Argument | 17 | 1.000 | 1.000 | 1.000 | 0.816 | No |
| Evidence (4-way) | 18 | 1.000 | 1.000 | 1.000 | 0.824 | No |
| Citation | 22 | 1.000 | 1.000 | 1.000 | 0.851 | No |
| Hallucination units | 4 | 1.000 | 1.000 | 1.000 | 0.510 | No |
| Coach refusal | 4 | 1.000 | 1.000 | 1.000 | 0.510 | No |

## 3. Other measured artefacts

| Item | Result |
| --- | --- |
| Hallucination red-team | 0 escaped / 1210 should-block (combinatorial; not live LLM) |
| Citation parser robustness | 2440 unlabeled strings, 0 exceptions; **not F1** |
| Reviewer κ | n=0, unmeasured |
| Crossref/OpenAlex/S2 precision | null; empty lookup = could_not_verify |
| Live OpenAI/Anthropic/Gemini | unproven, 0/3 keys, n_run=0 |
| Prompt v1.1.0 live regression | deploy **rejected** (accuracy null) |
| Calibration | ECE 0 on n=55 hard labels as p=1.0; **not exposed**; fail n≥1000 |

## 4. Template gold (consistency only)

Question 4320 F1 1.00; thesis 4032 F1 1.00; argument 3648 F1 1.00; evidence 2880 F1 0.997; citation 55 F1 1.00; rubric 96 F1 1.00. All `source: circular`.

## 5. Certification checklist

| Gate | Pass |
| --- | --- |
| Analyzers F1 CI low ≥0.98 on required n | **Fail** |
| Reference verification ≥0.98 | **Fail** |
| Live hallucination <0.5% | **Fail** |
| Schema compliance >99.9% live | **Fail** |
| Reviewer agreement documented | **Fail** |
| CIs reported | Pass (reporting) |
| Overall 98 | **Fail** |

## Decision

**Not AI-quality certified at 98.** Score **87**. The evaluation is honest enough to refuse the claim. It is not large enough to support it.
