# Dataset expansion plan

Date: 2026-09-07

This plan does **not** generate 1000 labels from classifier templates.

## Current independent n

| Dataset | Have (held-out) | Required for 98 | Delta |
| --- | ---: | ---: | ---: |
| Question analysis | 35 | 1000 | 965 |
| Thesis detection | 20 | 1000 | 980 |
| Argument analysis | 17 | 1000 | 983 |
| Evidence classification | 18 | 1000 | 982 |
| Citation analysis | 22 labeled; 2440 unlabeled robustness | 2000 **labeled** | 1978 labeled |
| Rubric alignment | 0 independent; 96 circular | 1000 | 1000 |
| Reviewer dual labels | 0 | all held-out docs | all |

Disciplines already represented in the small held-out: business, economics, history/oral history, engineering, law, medicine, humanities, social science, science policy. Coverage is **token**, not powered.

## How to grow without circularity

1. Sample real (consented) undergraduate/postgraduate scripts across the nine discipline buckets. Store text separately from labels.
2. Two academic reviewers label each item using `reviewer_labels.schema.json`. Mark `uncertain=true` when they disagree or abstain.
3. AcademicCheck AI labels are written only after reviewers lock gold (or in a sealed split).
4. Do not derive gold from `COMMANDS`, `THESIS_MARKERS`, or citation regexes.
5. Stratify: strong/weak/missing thesis; implicit vs explicit; multiple theses; APA/MLA/Harvard/Chicago/IEEE; malformed/incomplete/mixed/repeated citations.
6. Keep a frozen test split. Prompt/model changes may not retune on that split.

## Uncertainty

Every JSONL row includes `uncertain`. Items with `uncertain=true` are reported separately and **do not** count toward the 98% F1 numerator as automatic successes.

## What we will not do

- Mint 1000 thesis strings from `This essay argues that {topic}`
- Use the unlabeled 2440 citation strings as F1 gold
- Fill `reviewer_labels.jsonl` with synthetic reviewers A/B

Until those 1000/2000 labeled items exist, certification remains fail.

Public corpora (PERSUADE, AAE, ASAP, TOEFL11) were audited in `docs/EVALUATION_BOARD.md`. None are drop-in gold. PERSUADE/AAE are conditional candidates for argument/thesis **after** license review and a 100–300 record remap. TOEFL11 is rejected for the four analyzers. Template gold remains circular.
