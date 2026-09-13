# AI quality evaluation

Measured 7 Sep 2026. Artifact: `backend/app/services/ai/eval_report.json`.

## Template gold (circular — not lecturer gold)

| Suite | Cases | Precision | Recall | F1 | 95% F1 CI low | Source |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Question analyzer | 4320 | 1.000 | 1.000 | 1.000 | 0.999 | circular |
| Thesis analyzer | 4032 | 1.000 | 1.000 | 1.000 | 0.999 | circular |
| Citation extractor | 55 | 1.000 | 1.000 | 1.000 | 0.935 | circular |
| Argument analyzer | 3648 | 1.000 | 1.000 | 1.000 | 0.999 | circular |
| Evidence analyzer | 2880 | 0.993 | 1.000 | 0.997 | 0.994 | circular |
| Rubric checker | 96 | 1.000 | 1.000 | 1.000 | 0.962 | circular |
| **Template total** | **15031** | | | | | |

Do not read 1.00 F1 as solved AI. Labels come from the same rules as the classifiers.

## Held-out gold (independent expert-constructed — still not lecturer-reviewed)

| Suite | Cases | Precision | Recall | F1 | 95% F1 CI low |
| --- | ---: | ---: | ---: | ---: | ---: |
| Held-out question | 35 | 1.000 | 1.000 | 1.000 | **0.901** |
| Held-out thesis | 20 | 1.000 | 1.000 | 1.000 | **0.839** |
| Held-out argument | 17 | 1.000 | 1.000 | 1.000 | **0.816** |
| Held-out evidence (4-way) | 18 | 1.000 | 1.000 | 1.000 | **0.824** |
| Held-out citation | 22 | 1.000 | 1.000 | 1.000 | **0.851** |
| Hallucination guard (units) | 4 | 1.000 | 1.000 | 1.000 | 0.510 |
| Coach refusal | 4 | 1.000 | 1.000 | 1.000 | 0.510 |
| **Held-out labeled total** | **120** | | | | |

Certification requires n≥1000 (citations ≥2000) **and** CI lower bound ≥0.98. None of these suites pass.

Evidence confusion matrix (held-out): diagonal 5 / 7 / 2 / 4 for supported / needs_citation / potentially_unsupported / cannot_determine. False positive rate 0, false negative rate 0 **on n=18 only**.

## Other measurements

- Hallucination red-team: 0/1210 escaped (combinatorial). Live LLM: not run.
- Citation parser robustness: 2440 unlabeled, 0 failures. Not an F1 score.
- Reviewer agreement: n=0.
- Reference verification precision/recall: null.
- Live providers: unproven.

## Certification

**Evidence-backed AI quality: 87 / 100.** Gate 98. **Fail. Do not claim 98%.**

See `docs/AI_CERTIFICATION.md` and `docs/AI_CERTIFICATION_READINESS.md`.
