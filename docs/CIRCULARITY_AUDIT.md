# Circularity audit

Date: 2026-09-07  
Artifact: `backend/app/services/ai/eval_report.json`

This audit separates **training/classification rules**, **evaluation data**, and **reported metrics**. Template F1 is not used for 98% certification.

## 1. Circular benchmark sources

| Source | Generator | Classifier | Why circular |
| --- | --- | --- | --- |
| `question_gold()` | `COMMANDS × TOPICS × stems` | `analyze_question` scans the same `COMMANDS` keys | Labels are the strings the detector searches for |
| `thesis_gold()` | Topic-fill of marker phrases (`this essay argues`, `this essay is about`, `Background on`) | `THESIS_MARKERS`, `TOPIC_LABEL`, `CONTESTABLE` | Labels instantiate the regexes |
| `argument_gold()` | Topic-fill of `because`/`therefore` vs `there is a literature on` | `REASON_MARKERS`, `DESCRIPTIVE_ONLY` | Same vocabulary |
| `evidence_gold()` | Topic-fill of `GDP grew by 7 percent` vs cited variants | `SPECIFIC_CLAIM`, `CITATION` | Same triggers |
| `rubric_gold()` | Score dicts vs name aliases | `rubric_covered` alias map | Expected names are the alias keys |
| `citation_gold()` | Hand-written strings that match `APA_PAREN` / narrative patterns | `analyze_citations` | Mostly the same regex language (n=55, still not independent) |

`eval_report.json` marks these suites `source: "circular"`. **`certifiable` is always false** for them.

## 2. Separation in force

| Layer | Location | Role |
| --- | --- | --- |
| Training / decision rules | `question.py` `COMMANDS`; `classifiers.py` regexes; `citations.py` patterns; `hallucination.py` snippet-in-allowed | Production logic |
| Circular eval | `eval.py` `*_gold()` | Consistency / regression only |
| Independent eval | `heldout.py` + `heldout_extra.py` | Expert-constructed, not generated from templates |
| Red-team (not gold) | `hallucination_suite.py` | Adversarial strings; not lecturer labels |
| Unlabeled robustness | `citation_corpus.py` (n=2440) | Parser crash test; **no F1** |
| Human labels | `reviewer_labels.jsonl` | Empty by design until real reviewers write rows |

## 3. Evaluation examples must not be minted from classifier rules

Forbidden for 98% claims:

- Expanding `question_gold` / `thesis_gold` until n≥1000 and calling that held-out
- Using `COMMANDS × TOPICS` as “independent” question gold
- Scoring the citation parser against strings generated from `APA_PAREN`

Allowed:

- Hand-written academic prompts and paragraphs (current held-out)
- Lecturer dual annotation into `reviewer_labels.jsonl`
- Combinatorial hallucination **block** cases (red-team, not student gold)
- Unlabeled parser corpora

## 4. Current held-out (independent, still not lecturer gold)

| Suite | n | Point F1 | 95% F1 CI low | Certifiable |
| --- | ---: | ---: | ---: | --- |
| Question | 35 | 1.000 | 0.901 | No |
| Thesis | 20 | 1.000 | 0.839 | No |
| Argument | 17 | 1.000 | 0.816 | No |
| Evidence | 18 | 1.000 | 0.824 | No |
| Citation | 22 | 1.000 | 0.851 | No |

n is far below 1000 / 2000. Perfect point F1 on these sizes **does not** support a 98% claim: every CI lower bound is below 0.95.

## 5. Decision

Circular suites remain in CI as **regression guards**. They are excluded from certification. Do not report template F1 1.00 as AI quality.
